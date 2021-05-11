/* eslint-env browser */
/* eslint no-undef: "error" */
/* global moment */
/* global easytimer */

moment.locale("en");

const DATE_FORMATS = {
  visavail: "YYYY-MM-DD HH:mm:ss",
  metadata: "YYYY-MM-DD",
  picker: "DD/MM/YYYY",
}
const DEFAULT_MESSAGE_OF_THE_DAY = "Message of the day: [PENDING]";

const countdownNumberEl = document.getElementById("countdown-number");
const progress = document.querySelector("#countdown-progress");
const messageOfTheDayEl = document.getElementById("message-of-the-day");

let config;
let generatedCharts;
let charts;
let chartOptions;
let serialsMeta;
let serialsStats;

const today = new Date();
const yesterday = new Date();
yesterday.setDate(today.getDate() - 1);

let fromDate = moment(yesterday);
let toDate = moment(yesterday);

const timer = new easytimer.Timer();

const defaultOptions = {
    margin: {
        right: 60,
        left: 50,
        top: 30,
        bottom: 0
    },
    padding: {
        top: 0,
        bottom: 0,
        right: 45,
        left: 2
    },
    reduce_space_wrap: 2000000000,
    title: {
        enabled: false
    },
    sub_title: {
        enabled: false
    },
    legend: {
        enabled: false
    },
    y_title_tooltip: {
        enabled: false
    },
    icon: {
        classHasData: "fas fa-fw fa-check",
        classHasNoData: "fas fa-fw fa-exclamation-circle"
    },
    responsive: {
        enabled: false,
    },
    line_spacing: 3,
    ticks_for_graph: 2,
    graph: {
        height: 35
    },
    y_percentage: {
        enabled: true,
        custom_percentage: true
    },
    responsive: {
        enabled: true
    }
};

function setMessageOfTheDay() {
  messageOfTheDayEl.textContent = config.MessageOfTheDay || DEFAULT_MESSAGE_OF_THE_DAY;
}

function updateDatetime() {
  const date = new Date();
  const dateDiv = document.getElementById("date");
  const timeDiv = document.getElementById("time");
  dateDiv.textContent = moment(date).format("YYYY / MM / DD");
  timeDiv.textContent = moment(date).format("HH:mm:ss");
}

function startDatetimeClock() {
  updateDatetime();
  setInterval(updateDatetime, 1000);
}

function updateCountdownProgress(seconds) {
  const period = config.frequency_secs;
  const timePct = period !== 0 ? seconds/period : 0;
  const total = Math.PI * (2 * progress.r.baseVal.value);
  const progressPct = (1 - timePct) * total;
  progress.style.strokeDashoffset = progressPct;
}

function resetCountdown() {
  countdownNumberEl.textContent = config.frequency_secs;
  updateCountdownProgress(config.frequency_secs);
}

function onTimerStarted(event) {
  resetCountdown();
}

function onTimerSecondsUpdated(event) {
  const { detail } = event;
  const { timer: t } = detail;
  const { seconds } = t.getTimeValues();
  countdownNumberEl.textContent = seconds;
  updateCountdownProgress(seconds);
}

function onTimerTargetAchieved() {
  timer.reset();
  fetchSerialsMeta();
}

function onTimerReset(event) {
  resetCountdown();
}

function getTimerConfig(seconds) {
  return {
    startValues: { seconds },
    target: { seconds: 0 },
    precision: "seconds",
    countdown: true,
  };
}

function resetState() {
    config = null;
    generatedCharts = false;
    charts = [];
    chartOptions = [];
    serialsMeta = [];
    serialsStats = [];
}

function initDateRange() {
  $("input[name=\"date-range\"]").daterangepicker({
    opens: "left",
    locale: {
      format: DATE_FORMATS.picker,
    },
    ranges: {
        "Today": [moment(), moment()],
        "Yesterday": [moment().subtract(1, "days"), moment().subtract(1, "days")],
        "Last 7 Days": [moment().subtract(6, "days"), moment()],
        "Last 30 Days": [moment().subtract(29, "days"), moment()],
        "This Week": [moment().startOf("week"), moment().endOf("week")],
        "Last Week": [
          moment().subtract(1, "week").startOf("week"),
          moment().subtract(1, "week").endOf("week")
        ],
        "This Month": [moment().startOf("month"), moment().endOf("month")],
        "Last Month": [
          moment().subtract(1, "month").startOf("month"),
          moment().subtract(1, "month").endOf("month")
        ]
    },
    startDate: fromDate.format(DATE_FORMATS.picker),
    endDate: toDate.format(DATE_FORMATS.picker),
    buttonClasses: "btn",
    applyButtonClasses: "btn-success",
    cancelButtonClasses: "btn-danger",
  }, function(newFromDate, newToDate, label) {
    fromDate = newFromDate;
    toDate = newToDate;
  });

  $("input[name=\"date-range\"]").on("apply.daterangepicker", function(ev, picker) {
      $(this).val(
        picker.startDate.format(DATE_FORMATS.picker)
        + " - "
        + picker.endDate.format(DATE_FORMATS.picker)
      );
      onTimerTargetAchieved();
  });
}

function initTimer() {
  timer.addEventListener("secondsUpdated", onTimerSecondsUpdated);
  timer.addEventListener("started", onTimerStarted);
  timer.addEventListener("targetAchieved", onTimerTargetAchieved);
  timer.addEventListener("reset", onTimerReset);
}

function showLoadingSpinner() {
  document.getElementById('loading-spinner-container').style.display = 'flex';
}

function hideLoadingSpinner() {
  document.getElementById('loading-spinner-container').style.display = 'none';
}

function fetchConfig() {
    fetch("/config")
        .then(response => response.json())
        .then(response => {
            const { frequency_secs } = response;
            config = response;

            fetchSerialsMeta();
            setMessageOfTheDay();

            const timerConfig = getTimerConfig(frequency_secs);
            timer.start(timerConfig);
        })
        .catch(err => console.error(err));
}

function fetchSerialsMeta() {
    const url = new URL(window.location + "dashboard_metadata");
    const queryParams = new URLSearchParams();
    const fromDateStr = fromDate.format(DATE_FORMATS.metadata);
    const toDateStr = toDate.format(DATE_FORMATS.metadata);
    queryParams.set("from_date", fromDateStr);
    queryParams.set("to_date", toDateStr);
    url.search = queryParams.toString();

    console.log(`Fetching serials metadata from ${fromDateStr} to ${toDateStr}.`);

    clearCharts();
    showLoadingSpinner();

    fetch(url)
      .then(response => response.json())
      .then(response => {
        const { dashboard_metadata } = response;
        serialsMeta = dashboard_metadata;
        fetchSerialsStats();
      })
      .catch(error => {
        hideLoadingSpinner();
        console.log(error);
      })
}

function fetchSerialsStats() {
  // TODO: we need to multiple gap_seconds by 5
  const stripParticipant = (  // extract only needed fields
    {serial_id, platform_id, start, end, gap_seconds}
  ) => (
    {serial_id, platform_id, start, end, gap_seconds: gap_seconds * 5}
  );

  const serialParticipants = serialsMeta
    .filter(m => m.record_type === "SERIAL PARTICIPANT")
    .map(stripParticipant);
  const rangeTypes = ["G", "C"];

  const url = new URL(window.location + "dashboard_stats");

  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      serial_participants: serialParticipants,
      range_types: rangeTypes,
    })
  })
    .then(response => response.json())
    .then(response => {
        const { dashboard_stats } = response;
        serialsStats = dashboard_stats;
        renderCharts();
    })
    .catch(error => {
      hideLoadingSpinner();
      console.log(error);
    })
}

function calculatePercentageClass(number) {
    switch (true) {

        case number <= 25:
            return "red";
            break;
        case number <= 60:
            return "amber";
            break;
        case number <= 100:
            return "green";
            break;
        default:
            return "ypercentage";

    }
}

function addChartDiv(index, header, headerClass) {
    var newDiv = document.createElement("div");
    const htmlString = "<div class=\"card\"><div class=\"card-header text-center " +
        headerClass+ "\"><h5>" +
        header + "</h5></div><div style=\"overflow: hidden;\" class=\"visavail\" id=\"visavail_container_new_" +
        index +
        "\"><p id=\"visavail_graph_new_" +
        index +
        "\"></p></div></div>";
    newDiv.innerHTML = htmlString.trim();
    newDiv.classList.add("col-md-3");
    newDiv.classList.add("col-xl-2");
    newDiv.classList.add("p-1");

    var chartContainer = document.getElementById("chart-container");
    chartContainer.appendChild(newDiv);
}

function sortParticipants(p1, p2) {
  if (p1.force_type_name > p2.force_type_name) return 1;
  if (p1.force_type_name < p2.force_type_name) return -1;
  if (p1.name > p2.name) return 1;
  if (p1.name < p2.name) return -1;
}

function transformParticipant(participant, serial) {
    participant.serial_name = serial.name;
    participantStats = serialsStats.filter(
        s => s.resp_platform_id === participant.platform_id
        && s.resp_serial_id === participant.serial_name
    )
    let periods = participantStats.map(s => ([
            moment(s.resp_start_time).format(DATE_FORMATS.visavail),
            Number(s.resp_range_type === "C"),
            moment(s.resp_end_time).format(DATE_FORMATS.visavail),
        ]));
    participant.coverage = periods;

    const totalParticipation = participantStats
        .map(s => new Date(s.resp_end_time) - new Date(s.resp_start_time))
        .reduce((s, d) => s + d, 0);
    const totalCoverage = participantStats
        .filter(s => s.resp_range_type === "C")
        .map(s => new Date(s.resp_end_time) - new Date(s.resp_start_time))
        .reduce((s, d) => s + d, 0);
    participant["percent-coverage"] = totalParticipation !== 0 ? 100 * totalCoverage / totalParticipation : 0;
    participant["platform-type"] = participant["platform_type_name"];

    return {
        measure: participant.name,
        icon: {
            url: getParticipantIconUrl(participant),
            width: 32,
            height: 32,
            padding: {
                left: 0,
                right: 8
            },
            background_color: participant["force_type_color"]
        },
        percentage: {
            num: participant["percent-coverage"],
            measure: Math.round(participant["percent-coverage"]) + "%",
            class: "ypercentage_" + calculatePercentageClass(participant["percent-coverage"])
        },
        data: periods
    }
}

function transformSerials() {
    const serials = serialsMeta.filter(m => m.record_type === "SERIALS");
    const participants = serialsMeta.filter(m => m.record_type === "SERIAL PARTICIPANT");

    const transformedData = serials.map(serial => {
        let currSerialParticipants = participants
          .filter(p => p.serial_id === serial.serial_id)
          .sort(sortParticipants)
        currSerialParticipants = currSerialParticipants.map(p => transformParticipant(p, serial));
        serial.participants = currSerialParticipants;
        serial["overall_average"] = currSerialParticipants.length
            ? (
                currSerialParticipants
                  .map(p => p.percentage.num)
                  .reduce((s, d) => s + d, 0)
                / currSerialParticipants.length
            )
            : 0;
        serial.includeInTimeline = true;  // this should come from the database
        return serial;
    })
    return transformedData;
}

function renderCharts() {
    const transformedSerials = transformSerials();
    console.log("transformedSerials: ", transformedSerials);

    hideLoadingSpinner();

    console.log('Generating charts.');

    for (i = 0; i < transformedSerials.length; i++) {
        console.log(transformedSerials[i].name, transformedSerials[i].overall_average);

        if (!transformedSerials[i].includeInTimeline) {
            console.log("Serial flag 'includeInTimeline' false, won't generate chart.");
            continue;
        }

        chartOptions.push({...defaultOptions});
        addChartDiv(
            i + 1,
            transformedSerials[i].name,
            "" + calculatePercentageClass(transformedSerials[i].overall_average)
        );
        // override the target ids
        chartOptions[i].id_div_container = "visavail_container_new_" + (i + 1);
        chartOptions[i].id_div_graph = "visavail_graph_new_" + (i + 1);

        // create new chart instance
        charts[i] = visavail.generate(chartOptions[i], transformedSerials[i].participants);
    }
}

function clearCharts() {
  console.log('Clearing charts.');
  var chartContainer = document.getElementById("chart-container");
  chartContainer.innerHTML = "";
}

$(function() {
  resetState();
  initDateRange();
  initTimer();
  startDatetimeClock();
  fetchConfig();
});
