const RUN_WORKOUT_TYPES = new Set(["easy run", "long run", "tempo", "intervals"]);

const workoutForm = document.getElementById("workout-form");
const workoutList = document.getElementById("workout-list");
const workoutTemplate = document.getElementById("workout-item-template");
const runningFields = document.getElementById("running-fields");
const trainingFields = document.getElementById("training-fields");
const tcxFileInput = document.getElementById("tcx-file-input");
const importMessage = document.getElementById("import-message");
const importPreview = document.getElementById("import-preview");
const importPreviewDetails = document.getElementById("import-preview-details");
const saveImportButton = document.getElementById("save-import-button");
const cancelImportButton = document.getElementById("cancel-import-button");
const prevMonthButton = document.getElementById("prev-month");
const nextMonthButton = document.getElementById("next-month");
const calendarMonthLabel = document.getElementById("calendar-month-label");
const calendarWeekdays = document.getElementById("calendar-weekdays");
const calendarGrid = document.getElementById("calendar-grid");
const workoutDetailModal = document.getElementById("workout-detail-modal");
const workoutDetailDate = document.getElementById("workout-detail-date");
const workoutDetailContent = document.getElementById("workout-detail-content");
const closeDetailModalButton = document.getElementById("close-detail-modal");
const logSort = document.getElementById("log-sort");
const logFilter = document.getElementById("log-filter");

const totalWorkoutsElement = document.getElementById("total-workouts");
const currentWeekMilesElement = document.getElementById("current-week-miles");
const CALENDAR_WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
let calendarCursor = getMonthStart(new Date());
let pendingImportedWorkout = null;
let workoutsCache = [];
let selectedCalendarDate = null;

document.addEventListener("DOMContentLoaded", () => {
  initializeApp();
});

workoutForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const isRunWorkout = isRunType(workoutForm.workoutType.value);

  const workout = {
    id: createId(),
    date: workoutForm.date.value,
    workoutType: workoutForm.workoutType.value,
    plannedMiles: isRunWorkout ? toMilesValue(workoutForm.plannedMiles.value) : 0,
    actualMiles: isRunWorkout ? toMilesValue(workoutForm.actualMiles.value) : 0,
    plannedPace: isRunWorkout ? workoutForm.plannedPace.value.trim() : "",
    actualPace: isRunWorkout ? workoutForm.actualPace.value.trim() : "",
    exercises: isRunWorkout ? "" : workoutForm.exercises.value.trim(),
    totalMinutes: isRunWorkout ? 0 : toWholeMinutes(workoutForm.totalMinutes.value),
    notes: workoutForm.notes.value.trim()
  };

  const workouts = loadWorkouts();
  if (findDuplicateWorkout(workouts, workout)) {
    setImportMessage("This workout looks like a duplicate of an existing Garmin import.", "error");
    return;
  }

  try {
    const savedWorkout = await createWorkout(workout);
    workoutsCache.push(savedWorkout);
    workoutForm.reset();
    workoutForm.date.value = getTodayDate();
    syncWorkoutFields();
    setImportMessage("Workout saved.", "success");
    render();
  } catch (error) {
    setImportMessage(error.message || "Could not save the workout.", "error");
  }
});

workoutForm.addEventListener("reset", () => {
  window.setTimeout(() => {
    workoutForm.date.value = getTodayDate();
    syncWorkoutFields();
  }, 0);
});

workoutForm.workoutType.addEventListener("input", () => {
  syncWorkoutFields();
});

tcxFileInput.addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) {
    return;
  }

  try {
    const text = await file.text();
    const importedWorkout = parseTcxWorkout(text);
    const workouts = loadWorkouts();
    if (findDuplicateWorkout(workouts, importedWorkout)) {
      clearImportPreview();
      setImportMessage("This Garmin activity looks like a duplicate of an existing workout.", "error");
      tcxFileInput.value = "";
      return;
    }

    pendingImportedWorkout = importedWorkout;
    renderImportPreview(importedWorkout);
    setImportMessage("TCX file parsed successfully. Review the preview before saving.", "success");
  } catch (error) {
    clearImportPreview();
    setImportMessage(error.message || "Could not import that TCX file.", "error");
  }

  tcxFileInput.value = "";
});

saveImportButton.addEventListener("click", () => {
  saveImportedWorkout();
});

cancelImportButton.addEventListener("click", () => {
  clearImportPreview();
  setImportMessage("Garmin import canceled.", "success");
});

prevMonthButton.addEventListener("click", () => {
  calendarCursor = new Date(calendarCursor.getFullYear(), calendarCursor.getMonth() - 1, 1, 12, 0, 0);
  renderCalendar(loadWorkouts());
});

nextMonthButton.addEventListener("click", () => {
  calendarCursor = new Date(calendarCursor.getFullYear(), calendarCursor.getMonth() + 1, 1, 12, 0, 0);
  renderCalendar(loadWorkouts());
});

closeDetailModalButton.addEventListener("click", () => {
  closeWorkoutDetailModal();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !workoutDetailModal.classList.contains("is-hidden")) {
    closeWorkoutDetailModal();
  }
});

workoutDetailModal.addEventListener("click", (event) => {
  if (event.target === workoutDetailModal) {
    closeWorkoutDetailModal();
  }
});

logSort.addEventListener("input", () => {
  renderWorkoutList(loadWorkouts());
});

logFilter.addEventListener("input", () => {
  renderWorkoutList(loadWorkouts());
});

workoutList.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLButtonElement)) {
    return;
  }

  const workoutId = target.dataset.id;
  if (!workoutId) {
    return;
  }

  try {
    await deleteWorkout(workoutId);
    workoutsCache = workoutsCache.filter((workout) => workout.id !== workoutId);
    render();
  } catch (error) {
    setImportMessage(error.message || "Could not delete the workout.", "error");
  }
});

function render() {
  const workouts = loadWorkouts();
  renderHeaderStats(workouts);
  renderCalendar(workouts);
  renderWorkoutList(workouts);

  if (selectedCalendarDate && !workoutDetailModal.classList.contains("is-hidden")) {
    openWorkoutDetailModal(selectedCalendarDate);
  }
}

function renderHeaderStats(workouts) {
  totalWorkoutsElement.textContent = String(workouts.length);
  const currentWeekStart = startOfWeek(new Date());
  const currentWeekStats = getWeeklyStats(workouts, currentWeekStart);
  currentWeekMilesElement.textContent = formatMiles(currentWeekStats.actualMiles);
}

function renderWorkoutList(workouts) {
  const visibleWorkouts = getVisibleWorkouts(workouts);

  if (visibleWorkouts.length === 0) {
    workoutList.innerHTML = '<p class="empty-state">No workouts saved yet.</p>';
    return;
  }

  workoutList.innerHTML = "";

  for (const workout of visibleWorkouts) {
    const item = workoutTemplate.content.firstElementChild.cloneNode(true);
    item.querySelector(".workout-date").textContent = formatDate(workout.date);
    item.querySelector(".workout-type").textContent = workout.workoutType;

    const meta = isRunType(workout.workoutType)
      ? [
          `Planned miles: ${formatMiles(workout.plannedMiles)}`,
          `Actual miles: ${formatMiles(workout.actualMiles)}`,
          `Planned pace: ${workout.plannedPace || "-"}`,
          `Actual pace: ${workout.actualPace || "-"}`
        ]
      : [
          `Exercises: ${workout.exercises || "-"}`,
          `Total time: ${formatMinutes(workout.totalMinutes)}`
        ];

    if (workout.totalDurationMinutes) {
      meta.push(`Duration: ${formatMinutes(workout.totalDurationMinutes)}`);
    }

    if (workout.averageHeartRate) {
      meta.push(`Avg HR: ${workout.averageHeartRate} bpm`);
    }

    if (workout.calories) {
      meta.push(`Calories: ${workout.calories}`);
    }

    if (workout.source) {
      meta.push(`Source: ${workout.source}`);
    }

    const metaContainer = item.querySelector(".workout-meta");
    meta.forEach((entry) => {
      const chip = document.createElement("span");
      chip.className = "meta-chip";
      chip.textContent = entry;
      metaContainer.appendChild(chip);
    });

    const notes = item.querySelector(".workout-notes");
    notes.textContent = workout.notes || "No notes added.";

    const deleteButton = item.querySelector(".delete-button");
    deleteButton.dataset.id = workout.id;

    workoutList.appendChild(item);
  }
}

function renderCalendarWeekdays() {
  calendarWeekdays.innerHTML = "";

  for (const weekday of CALENDAR_WEEKDAYS) {
    const cell = document.createElement("div");
    cell.className = "calendar-weekday";
    cell.textContent = weekday;
    calendarWeekdays.appendChild(cell);
  }
}

function renderCalendar(workouts) {
  const monthStart = getMonthStart(calendarCursor);
  const calendarStart = startOfWeek(monthStart);
  const workoutDetailsByDay = groupCalendarDetailsByDay(workouts);
  const workoutsByDay = groupWorkoutsByDate(workouts);

  calendarMonthLabel.textContent = monthStart.toLocaleDateString(undefined, {
    month: "long",
    year: "numeric"
  });

  calendarGrid.innerHTML = "";

  for (let index = 0; index < 42; index += 1) {
    const currentDay = new Date(calendarStart);
    currentDay.setDate(calendarStart.getDate() + index);
    currentDay.setHours(12, 0, 0, 0);

    const dayKey = toDateKey(currentDay);
    const details = workoutDetailsByDay.get(dayKey);
    const dayWorkouts = workoutsByDay.get(dayKey) || [];
    const dayCell = document.createElement(dayWorkouts.length > 0 ? "button" : "article");
    dayCell.className = "calendar-day";

    if (currentDay.getMonth() !== monthStart.getMonth()) {
      dayCell.classList.add("is-outside-month");
    }

    if (dayKey === getTodayDate()) {
      dayCell.classList.add("is-today");
    }

    if (dayWorkouts.length > 0) {
      if (dayCell instanceof HTMLButtonElement) {
        dayCell.type = "button";
        dayCell.classList.add("calendar-day-button");
        dayCell.addEventListener("click", () => {
          openWorkoutDetailModal(dayKey);
        });
      }

      dayCell.classList.add("has-workout");
      dayCell.tabIndex = 0;
      dayCell.setAttribute("role", "button");
      dayCell.setAttribute("aria-label", `View workouts for ${formatDate(dayKey)}`);
      dayCell.dataset.workoutDate = dayKey;
    }

    const content = details ? renderCalendarDayContent(details) : "";
    dayCell.innerHTML = `
      <p class="calendar-day-number">${currentDay.getDate()}</p>
      ${content}
    `;

    calendarGrid.appendChild(dayCell);
  }
}

function loadWorkouts() {
  return [...workoutsCache];
}

async function initializeApp() {
  workoutForm.date.value = getTodayDate();
  syncWorkoutFields();
  renderCalendarWeekdays();

  try {
    await refreshWorkouts();
    render();
  } catch (error) {
    setImportMessage(error.message || "Could not load workouts from the local server.", "error");
  }
}

async function refreshWorkouts() {
  workoutsCache = await apiRequest("/api/workouts");
}

async function createWorkout(workout) {
  return apiRequest("/api/workouts", {
    method: "POST",
    body: JSON.stringify(workout)
  });
}

async function importWorkout(workout) {
  return apiRequest("/api/import-workout", {
    method: "POST",
    body: JSON.stringify(workout)
  });
}

async function deleteWorkout(workoutId) {
  return apiRequest(`/api/workouts/${encodeURIComponent(workoutId)}`, {
    method: "DELETE"
  });
}

async function saveImportedWorkout() {
  if (!pendingImportedWorkout) {
    return;
  }

  const workouts = loadWorkouts();
  if (findDuplicateWorkout(workouts, pendingImportedWorkout)) {
    clearImportPreview();
    setImportMessage("This Garmin activity looks like a duplicate of an existing workout.", "error");
    return;
  }

  try {
    const savedWorkout = await importWorkout(pendingImportedWorkout);
    workoutsCache.push(savedWorkout);
    setImportMessage(`Imported Garmin workout from ${formatDate(pendingImportedWorkout.date)}.`, "success");
    clearImportPreview();
    render();
  } catch (error) {
    setImportMessage(error.message || "Could not save the imported workout.", "error");
  }
}

async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  const contentType = response.headers.get("Content-Type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : null;

  if (!response.ok) {
    throw new Error(payload?.error || "Request failed.");
  }

  return payload;
}

function renderImportPreview(workout) {
  importPreviewDetails.innerHTML = "";

  const previewItems = [
    { label: "Date", value: formatDateTime(workout.importedAt) },
    { label: "Activity Type", value: workout.importedSport || workout.workoutType },
    { label: "Duration", value: formatMinutes(workout.totalDurationMinutes) },
    { label: "Distance", value: workout.actualMiles ? formatMiles(workout.actualMiles) : "-" },
    { label: "Average Heart Rate", value: workout.averageHeartRate ? `${workout.averageHeartRate} bpm` : "-" },
    { label: "Calories", value: workout.calories ? String(workout.calories) : "-" }
  ];

  for (const item of previewItems) {
    const chip = document.createElement("div");
    chip.className = "preview-chip";
    chip.innerHTML = `<strong>${item.label}</strong><span>${item.value}</span>`;
    importPreviewDetails.appendChild(chip);
  }

  importPreview.classList.remove("is-hidden");
}

function clearImportPreview() {
  pendingImportedWorkout = null;
  importPreviewDetails.innerHTML = "";
  importPreview.classList.add("is-hidden");
}

function parseTcxWorkout(xmlText) {
  const parser = new DOMParser();
  const xmlDocument = parser.parseFromString(xmlText, "application/xml");

  if (xmlDocument.getElementsByTagName("parsererror").length > 0) {
    throw new Error("That file is not a valid TCX XML file.");
  }

  const activity = getFirstElementByTag(xmlDocument, "Activity");
  if (!activity) {
    throw new Error("No activity was found in that TCX file.");
  }

  const activityId = getNodeText(activity, "Id");
  const sport = activity.getAttribute("Sport") || getNodeText(activity, "ActivityType") || "Other";
  const lapNodes = getElementsByTag(activity, "Lap");

  const totalSeconds = lapNodes.reduce((sum, lap) => sum + toNumber(getNodeText(lap, "TotalTimeSeconds")), 0);
  const totalMeters = lapNodes.reduce((sum, lap) => sum + toNumber(getNodeText(lap, "DistanceMeters")), 0);
  const calories = lapNodes.reduce((sum, lap) => sum + toNumber(getNodeText(lap, "Calories")), 0);

  let averageHeartRate = 0;
  for (const lap of lapNodes) {
    const heartRateNode = getFirstElementByTag(getFirstElementByTag(lap, "AverageHeartRateBpm"), "Value");
    if (heartRateNode) {
      averageHeartRate = Math.round(toNumber(heartRateNode.textContent));
      break;
    }
  }

  const firstLap = lapNodes[0] || null;
  const lapStartTime = firstLap ? firstLap.getAttribute("StartTime") : "";
  const startDate = parseImportedDate(activityId || lapStartTime);
  if (!startDate) {
    throw new Error("Could not find a valid activity date in that TCX file.");
  }

  const distanceMiles = metersToMiles(totalMeters);
  const totalMinutes = secondsToMinutes(totalSeconds);
  const workoutType = mapImportedWorkoutType(sport, distanceMiles);
  const notes = buildImportNotes({
    sport,
    totalMinutes,
    averageHeartRate,
    calories
  });

  const importedWorkout = {
    id: createId(),
    importedActivityId: activityId || startDate.toISOString(),
    date: toDateKey(startDate),
    workoutType,
    plannedMiles: 0,
    actualMiles: isRunType(workoutType) ? distanceMiles : 0,
    plannedPace: "",
    actualPace: isRunType(workoutType) ? formatPaceFromDistanceAndTime(distanceMiles, totalMinutes) : "",
    exercises: isRunType(workoutType) ? "" : sport,
    totalMinutes: isRunType(workoutType) ? 0 : totalMinutes,
    totalDurationMinutes: totalMinutes,
    averageHeartRate: averageHeartRate || 0,
    calories: calories || 0,
    notes,
    source: "garmin_import",
    importedSport: sport,
    importedAt: startDate.toISOString()
  };

  return importedWorkout;
}

function findDuplicateWorkout(workouts, candidateWorkout) {
  return workouts.some((workout) => {
    if (isPlanWorkout(workout) || isPlanWorkout(candidateWorkout)) {
      return false;
    }

    if (candidateWorkout.source !== "garmin_import" && workout.source !== "garmin_import") {
      return false;
    }

    if (workout.importedActivityId && candidateWorkout.importedActivityId) {
      return workout.importedActivityId === candidateWorkout.importedActivityId;
    }

    if (workout.date !== candidateWorkout.date) {
      return false;
    }

    const candidateIsRun = isWorkoutRunLike(candidateWorkout);
    const existingIsRun = isWorkoutRunLike(workout);

    if (candidateIsRun && existingIsRun) {
      const existingMiles = getWorkoutDistanceForDuplicateCheck(workout);
      const candidateMiles = getWorkoutDistanceForDuplicateCheck(candidateWorkout);

      if (!existingMiles || !candidateMiles) {
        return false;
      }

      return Math.abs(existingMiles - candidateMiles) <= 0.5;
    }

    if (!candidateIsRun && !existingIsRun) {
      const existingMinutes = getWorkoutMinutesForDuplicateCheck(workout);
      const candidateMinutes = getWorkoutMinutesForDuplicateCheck(candidateWorkout);

      if (!existingMinutes || !candidateMinutes) {
        return false;
      }

      return Math.abs(existingMinutes - candidateMinutes) <= 5;
    }

    return false;
  });
}

function groupCalendarDetailsByDay(workouts) {
  return workouts.reduce((map, workout) => {
    const dayKey = workout.date;
    const details = map.get(dayKey) || {
      plannedMiles: 0,
      actualMiles: 0,
      hasRunWorkout: false,
      nonRunItems: []
    };

    if (isRunType(workout.workoutType)) {
      details.plannedMiles += Number(workout.plannedMiles) || 0;
      details.actualMiles += Number(workout.actualMiles) || 0;
      details.hasRunWorkout = true;
    } else if (workout.workoutType === "strength" || workout.workoutType === "cross-training") {
      details.nonRunItems.push({
        workoutType: workout.workoutType,
        exercises: workout.exercises || workout.workoutType,
        totalMinutes: Number(workout.totalMinutes) || 0
      });
    }

    if (details.hasRunWorkout || details.nonRunItems.length > 0) {
      map.set(dayKey, details);
    }

    return map;
  }, new Map());
}

function groupWorkoutsByDate(workouts) {
  return workouts.reduce((map, workout) => {
    const list = map.get(workout.date) || [];
    list.push(workout);
    map.set(workout.date, list);
    return map;
  }, new Map());
}

function toMilesValue(value) {
  if (value === "") {
    return 0;
  }

  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function toNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function toWholeMinutes(value) {
  if (value === "") {
    return 0;
  }

  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.round(number)) : 0;
}

function getWeeklyStats(workouts, weekStartDate) {
  const weekStart = startOfWeek(weekStartDate);
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekEnd.getDate() + 6);

  return workouts.reduce((stats, workout) => {
    const workoutDate = new Date(`${workout.date}T12:00:00`);
    if (workoutDate < weekStart || workoutDate > weekEnd) {
      return stats;
    }

    stats.plannedMiles += Number(workout.plannedMiles) || 0;
    stats.actualMiles += Number(workout.actualMiles) || 0;

    const completed = RUN_WORKOUT_TYPES.has(workout.workoutType) && (Number(workout.actualMiles) || 0) > 0;
    if (completed) {
      stats.completedRuns += 1;
    }

    return stats;
  }, { plannedMiles: 0, actualMiles: 0, completedRuns: 0 });
}

function startOfWeek(date) {
  const normalized = new Date(date);
  const day = normalized.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  normalized.setDate(normalized.getDate() + diff);
  normalized.setHours(12, 0, 0, 0);
  return normalized;
}

function getTodayDate() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getMonthStart(date) {
  return new Date(date.getFullYear(), date.getMonth(), 1, 12, 0, 0);
}

function formatDate(dateString) {
  return new Date(`${dateString}T12:00:00`).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric"
  });
}

function formatDateTime(dateString) {
  return new Date(dateString).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

function formatMiles(value) {
  return `${Number(value || 0).toFixed(1)} mi`;
}

function formatMinutes(value) {
  return `${Number(value || 0)} min`;
}

function formatPaceFromDistanceAndTime(distanceMiles, totalMinutes) {
  if (!distanceMiles || !totalMinutes) {
    return "";
  }

  const minutesPerMile = totalMinutes / distanceMiles;
  const wholeMinutes = Math.floor(minutesPerMile);
  const seconds = Math.round((minutesPerMile - wholeMinutes) * 60);
  const normalizedMinutes = seconds === 60 ? wholeMinutes + 1 : wholeMinutes;
  const normalizedSeconds = seconds === 60 ? 0 : seconds;
  return `${normalizedMinutes}:${String(normalizedSeconds).padStart(2, "0")}/mi`;
}

function renderCalendarDayContent(details) {
  if (details.hasRunWorkout) {
    const chips = [];

    if (details.plannedMiles > 0) {
      chips.push(`<div class="calendar-mile-chip">Planned: ${formatMiles(details.plannedMiles)}</div>`);
    }

    if (details.actualMiles > 0) {
      chips.push(`<div class="calendar-mile-chip">Actual: ${formatMiles(details.actualMiles)}</div>`);
    }

    if (chips.length === 0) {
      return "";
    }

    return `
      <div class="calendar-day-miles">
        ${chips.join("")}
      </div>
    `;
  }

  const nonRunItems = details.nonRunItems
    .map((item) => {
      const label = item.exercises || item.workoutType;
      return `<div class="calendar-mile-chip">${label} (${formatMinutes(item.totalMinutes)})</div>`;
    })
    .join("");

  return `<div class="calendar-day-miles">${nonRunItems}</div>`;
}

function openWorkoutDetailModal(dateKey) {
  selectedCalendarDate = dateKey;
  const workouts = loadWorkouts()
    .filter((workout) => workout.date === dateKey)
    .sort((a, b) => workoutSortOrder(a) - workoutSortOrder(b));

  workoutDetailDate.textContent = formatDate(dateKey);
  workoutDetailContent.innerHTML = "";

  for (const workout of workouts) {
    const detailItem = document.createElement("article");
    detailItem.className = "detail-item";

    const meta = buildWorkoutMeta(workout);
    const metaHtml = meta.map((entry) => `<span class="meta-chip">${entry}</span>`).join("");

    detailItem.innerHTML = `
      <div class="detail-item-header">
        <div>
          <h3 class="detail-item-title">${workout.planLabel || workout.workoutType}</h3>
          <p class="summary-label">${getWorkoutSourceLabel(workout)}</p>
        </div>
      </div>
      <div class="detail-meta">${metaHtml}</div>
      <p class="detail-notes">${workout.notes || "No notes added."}</p>
    `;

    workoutDetailContent.appendChild(detailItem);
  }

  workoutDetailModal.classList.remove("is-hidden");
  workoutDetailModal.setAttribute("aria-hidden", "false");
}

function closeWorkoutDetailModal() {
  selectedCalendarDate = null;
  workoutDetailModal.classList.add("is-hidden");
  workoutDetailModal.setAttribute("aria-hidden", "true");
  workoutDetailContent.innerHTML = "";
  workoutDetailDate.textContent = "";
}

function buildWorkoutMeta(workout) {
  const meta = isRunType(workout.workoutType)
    ? [
        `Planned miles: ${formatMiles(workout.plannedMiles)}`,
        `Actual miles: ${formatMiles(workout.actualMiles)}`,
        `Planned pace: ${workout.plannedPace || "-"}`,
        `Actual pace: ${workout.actualPace || "-"}`
      ]
    : [
        `Exercises: ${workout.exercises || "-"}`,
        `Total time: ${formatMinutes(workout.totalMinutes)}`
      ];

  if (workout.totalDurationMinutes) {
    meta.push(`Duration: ${formatMinutes(workout.totalDurationMinutes)}`);
  }

  if (workout.averageHeartRate) {
    meta.push(`Avg HR: ${workout.averageHeartRate} bpm`);
  }

  if (workout.calories) {
    meta.push(`Calories: ${workout.calories}`);
  }

  return meta;
}

function getWorkoutSourceLabel(workout) {
  if (workout.source === "plan") {
    return `Planned workout${workout.planWeek ? ` • ${workout.planWeek} weeks to go` : ""}`;
  }

  if (workout.source === "garmin_import") {
    return "Garmin import";
  }

  return "Manual entry";
}

function workoutSortOrder(workout) {
  const order = {
    strength: 0,
    "cross-training": 1,
    "easy run": 2,
    tempo: 3,
    intervals: 4,
    "long run": 5
  };

  return order[workout.workoutType] ?? 99;
}

function getVisibleWorkouts(workouts) {
  const filterValue = logFilter.value;
  const sortValue = logSort.value;

  const filtered = filterValue === "all"
    ? [...workouts]
    : workouts.filter((workout) => workout.workoutType === filterValue);

  filtered.sort((a, b) => {
    const compare = a.date.localeCompare(b.date);
    return sortValue === "asc" ? compare : -compare;
  });

  return filtered;
}

function toDateKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function isRunType(workoutType) {
  return RUN_WORKOUT_TYPES.has(workoutType);
}

function isWorkoutRunLike(workout) {
  return isRunType(workout.workoutType);
}

function isPlanWorkout(workout) {
  return workout.source === "plan";
}

function getWorkoutDistanceForDuplicateCheck(workout) {
  return Number(workout.actualMiles) || Number(workout.plannedMiles) || 0;
}

function getWorkoutMinutesForDuplicateCheck(workout) {
  return Number(workout.totalMinutes) || Number(workout.totalDurationMinutes) || 0;
}

function mapImportedWorkoutType(sport, distanceMiles) {
  const normalizedSport = sport.toLowerCase();
  if (normalizedSport.includes("running")) {
    return distanceMiles >= 10 ? "long run" : "easy run";
  }

  if (normalizedSport.includes("biking") || normalizedSport.includes("cycling") || normalizedSport.includes("elliptical")) {
    return "cross-training";
  }

  if (normalizedSport.includes("strength")) {
    return "strength";
  }

  return "cross-training";
}

function metersToMiles(meters) {
  return meters / 1609.344;
}

function secondsToMinutes(seconds) {
  return Math.round(seconds / 60);
}

function getNodeText(parent, tagName) {
  const node = getFirstElementByTag(parent, tagName);
  return node ? node.textContent.trim() : "";
}

function parseImportedDate(rawValue) {
  if (!rawValue) {
    return null;
  }

  const parsed = new Date(rawValue);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function buildImportNotes({ sport, totalMinutes, averageHeartRate, calories }) {
  const parts = [`Imported from Garmin TCX (${sport})`];

  if (totalMinutes) {
    parts.push(`Duration ${formatMinutes(totalMinutes)}`);
  }

  if (averageHeartRate) {
    parts.push(`Avg HR ${averageHeartRate} bpm`);
  }

  if (calories) {
    parts.push(`Calories ${calories}`);
  }

  return parts.join(" | ");
}

function setImportMessage(message, tone) {
  importMessage.textContent = message;
  importMessage.classList.remove("is-success", "is-error");

  if (tone === "success") {
    importMessage.classList.add("is-success");
  }

  if (tone === "error") {
    importMessage.classList.add("is-error");
  }
}

function getFirstElementByTag(parent, tagName) {
  if (!parent) {
    return null;
  }

  return parent.getElementsByTagNameNS("*", tagName)[0] || null;
}

function getElementsByTag(parent, tagName) {
  if (!parent) {
    return [];
  }

  return Array.from(parent.getElementsByTagNameNS("*", tagName));
}

function syncWorkoutFields() {
  const runWorkout = isRunType(workoutForm.workoutType.value);

  runningFields.classList.toggle("is-hidden", !runWorkout);
  trainingFields.classList.toggle("is-hidden", runWorkout);

  if (runWorkout) {
    workoutForm.exercises.value = "";
    workoutForm.totalMinutes.value = "";
    return;
  }

  workoutForm.plannedMiles.value = "";
  workoutForm.actualMiles.value = "";
  workoutForm.plannedPace.value = "";
  workoutForm.actualPace.value = "";
}

function createId() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
