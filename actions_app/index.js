const [CONTEXTS, PEOPLE, actions] = JSON.parse(
    document.getElementById("actionsData").textContent.trim(),
);

// Same as `dashboards/utils.py:format_date`
const formatDate = (dateStr, timeStr, currentDate, connective) => {
    // Need to force this into the local timezone
    const date = new Date(`${dateStr}T00:00:00`);
    const weekdays = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ];

    const daysDifference = Math.floor(
        (date - currentDate) / (1000 * 60 * 60 * 24),
    );

    let dayStr = "";
    if (daysDifference === 0) {
        dayStr = "today";
    } else if (daysDifference === 1) {
        dayStr = "tomorrow";
    } else if (daysDifference === -1) {
        dayStr = "yesterday";
    } else if (2 <= daysDifference && daysDifference < 7) {
        dayStr = `${connective} ${weekdays[date.getDay()]}`;
    } else if (-7 < daysDifference && daysDifference < 0) {
        dayStr = `last ${weekdays[date.getDay()]}`;
    } else if (0 < daysDifference && daysDifference < 14) {
        dayStr = `next ${weekdays[date.getDay()]}`;
    } else {
        dayStr = `${connective} ${weekdays[date.getDay()]} ${dateStr}`;
    }

    if (timeStr) {
        dayStr += ` at ${timeStr}`;
    }

    return dayStr;
};

// Same as `urgent.py:filter_to_urgent`.
const getUrgent = (date, proximityDays) => {
    date.setHours(0, 0, 0, 0);

    const cutoffDate = new Date(date);
    cutoffDate.setDate(cutoffDate.getDate() + proximityDays);
    cutoffDate.setHours(23, 59, 59, 999);

    const urgent = [];
    for (
        const [
            html,
            scheduled,
            deadline,
            _ctxs,
            _people,
            _focus,
            _time,
            _keyword,
        ] of actions
    ) {
        if (!deadline) {
            continue;
        }

        // Must be sure to have times, otherwise these are treated as UTC!
        const deadlineDate = new Date(
            `${deadline[0]}T${deadline[1] ? deadline[1] : "00:00:00"}`,
        );
        const scheduledDate = scheduled
            ? new Date(
                `${scheduled[0]}T${scheduled[1] ? scheduled[1] : "00:00:00"}`,
            )
            : null;

        if (scheduledDate && scheduledDate > date) {
            continue;
        }
        if (deadlineDate > cutoffDate) {
            continue;
        }

        let fullHtml = html;
        if (scheduled) {
            const scheduledReadable = formatDate(
                scheduled[0],
                scheduled[1],
                date,
                "for",
            );
            fullHtml = fullHtml.replace("{{ scheduled }}", scheduledReadable);
        }
        if (deadline) {
            const deadlineReadable = formatDate(
                deadline[0],
                deadline[1],
                date,
                "on",
            );
            fullHtml = fullHtml.replace("{{ deadline }}", deadlineReadable);
        }
        urgent.push(fullHtml);
    }

    // Already sorted!
    return urgent;
};

// Same as `utils.py:validate_time`.
const parseTimeStr = (timeStr) => {
    if (!timeStr) {
        return null;
    }

    const parts = timeStr.split(":");

    let total_minutes = 0;
    for (const part of parts) {
        if (part.endsWith("hr")) {
            total_minutes += parseInt(part.slice(0, -2)) * 60;
        } else if (part.endsWith("m")) {
            total_minutes += parseInt(part.slice(0, -1));
        } else {
            throw new Error(`Invalid time part: ${part}`);
        }
    }

    return total_minutes;
};

// Same as `filter.py:filter_next_actions`.
const filter = (date, contextsArr, peopleArr, maxTimeStr, maxFocus, ty) => {
    date.setHours(0, 0, 0, 0);

    const until = new Date(date);
    until.setHours(23, 59, 59, 999);

    const contexts = contextsArr
        ? new Set(contextsArr.map((ctx) => CONTEXTS.indexOf(ctx)))
        : null;
    const people = peopleArr
        ? new Set(peopleArr.map((person) => PEOPLE.indexOf(person)))
        : null;
    const maxTime = parseTimeStr(maxTimeStr);

    const filtered = [];
    for (
        const [
            html,
            scheduled,
            deadline,
            ctxs,
            actionPeople,
            focus,
            time,
            keyword,
        ] of actions
    ) {
        if (ty == "tasks" && keyword != "TODO") {
            continue;
        }
        if (ty == "problems" && keyword != "PROB") {
            continue;
        }

        if (contexts) {
            let weHaveAll = true;
            let itemHasOne = false;
            for (const ctxIdx of ctxs) {
                if (!contexts.has(ctxIdx)) {
                    weHaveAll = false;
                    break;
                } else {
                    itemHasOne = true;
                }
            }
            if (!weHaveAll || !itemHasOne) {
                continue;
            }
        }
        if (people) {
            let weHaveAll = true;
            let itemHasOne = false;
            for (const personIdx of actionPeople) {
                if (!people.has(personIdx)) {
                    weHaveAll = false;
                    break;
                } else {
                    itemHasOne = true;
                }
            }
            if (!weHaveAll || !itemHasOne) {
                continue;
            }
        }
        if (maxTime && time > maxTime) {
            continue;
        }
        if (maxFocus !== null && focus > maxFocus) {
            continue;
        }

        let fullHtml = html;
        if (scheduled) {
            const scheduledDate = scheduled
                ? new Date(
                    `${scheduled[0]}T${
                        scheduled[1] ? scheduled[1] : "00:00:00"
                    }`,
                )
                : null;
            if (scheduledDate && scheduledDate > date) {
                continue;
            }

            const scheduledReadable = formatDate(
                scheduled[0],
                scheduled[1],
                date,
                "for",
            );
            fullHtml = fullHtml.replace("{{ scheduled }}", scheduledReadable);
        }
        if (deadline) {
            const deadlineReadable = formatDate(
                deadline[0],
                deadline[1],
                date,
                "on",
            );
            fullHtml = fullHtml.replace("{{ deadline }}", deadlineReadable);
        }
        filtered.push(fullHtml);
    }

    return filtered;
};

// Displays the given list of HTML for actions on the page.
const displayActions = (actionsHtml) => {
    const actionsEl = document.getElementById("actions");
    actionsEl.innerHTML = actionsHtml.join("");
};

// Function called from HTML that runs the filter and displays results.
const doFilter = () => {
    const maxTimeStr = document.getElementById("time").value;
    // `<select>`, so guaranteed to be right
    const maxFocus = parseInt(document.getElementById("focus").value);
    const contexts = Array.from(
        document.getElementById("contextsSelect").selectedOptions,
    ).map((option) => option.value);
    const people = Array.from(
        document.getElementById("peopleSelect").selectedOptions,
    ).map((option) => option.value);
    let ty = "all";
    for (const radio of document.getElementsByName("ty")) {
        if (radio.checked) {
            ty = radio.value;
            break;
        }
    }

    const filtered = filter(
        new Date(),
        contexts.length === 0 ? null : contexts,
        people.length === 0 ? null : people,
        maxTimeStr ? maxTimeStr : null,
        maxFocus != -1 ? maxFocus : null,
        ty,
    );
    displayActions(filtered);
};

// Populate the context/people dropdowns with the right options
const contextSelect = document.getElementById("contextsSelect");
for (const ctx of CONTEXTS) {
    const option = document.createElement("option");
    option.value = ctx;
    option.innerText = ctx.charAt(0).toUpperCase() + ctx.slice(1);
    contextSelect.appendChild(option);
}
const peopleSelect = document.getElementById("peopleSelect");
for (const person of PEOPLE) {
    const option = document.createElement("option");
    option.value = person;
    option.innerText = person;
    peopleSelect.appendChild(option);
}
// Initially, display the urgent actions so the user always sees them before any search
// and can see them quickly by default
displayActions(getUrgent(new Date(), 3));
