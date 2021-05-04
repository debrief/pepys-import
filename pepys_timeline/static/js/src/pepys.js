moment.locale("en");

const DATETIME_FORMAT = "YYYY-MM-DD HH:mm:ss";

let generatedCharts = false;
let charts;
let chartOptions;
let serialsMeta;
let serialsStats;

function resetState() {
    charts = [];
    chartOptions = [];
    serialsMeta = [];
    serialsStats = [];
}

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
        class_has_data: 'fas fa-fw fa-check',
        class_has_no_data: 'fas fa-fw fa-exclamation-circle'
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


function onDataReceived() {
    console.log('on data received');
}

function fetchConfig() {
    fetch('/config')
        .then(response => response.json())
        .then(response => {
            const { frequency_secs } = response;
            fetchSerialsMeta();
            setInterval(fetchSerialsMeta, frequency_secs * 1000);

        })
        .catch(err => console.error(err));
}

function fetchSerialsMeta() {
    console.log('fetching serials metadata');

    const url = new URL(window.location + 'dashboard_metadata');
    const queryParams = new URLSearchParams();
    queryParams.set('from_date', '2021-01-05');
    queryParams.set('to_date', '2021-01-05');
    url.search = queryParams.toString();

    fetch(url)
      .then(response => response.json())
      .then(response => {
        const { dashboard_metadata } = response;
        console.log('testing dashboard_metadata', response);
        serialsMeta = dashboard_metadata;
        fetchSerialsStats();
      }
    )
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

  const url = new URL(window.location + 'dashboard_stats');

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      serial_participants: serialParticipants,
      range_types: rangeTypes,
    })
  })
    .then(response => response.json())
    .then(response => {
        console.log('testing dashboard_stats', response);
        const { dashboard_stats } = response;
        serialsStats = dashboard_stats;
        renderCharts();
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

    };
}

function addChartDiv(index, header, header_class) {
    var newDiv = document.createElement('div');
    htmlString = '<div class="card"><div class="card-header text-center '+header_class+'"><h5>'+header+'</h5></div><div style="overflow: hidden;" class="visavail" id="visavail_container_new_'+index+'"><p id="visavail_graph_new_'+index+'"></p></div></div>'
    newDiv.innerHTML = htmlString.trim();
    newDiv.classList.add("col-md-3")
    newDiv.classList.add("col-xl-2")
    newDiv.classList.add("p-1")

    var chartDiv = document.getElementById("chart_row");
    chartDiv.appendChild(newDiv);
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
            moment(s.resp_start_time).format(DATETIME_FORMAT),
            Number(s.resp_range_type === "C"),
            moment(s.resp_end_time).format(DATETIME_FORMAT),
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
    clearCharts();
    const transformedSerials = transformSerials();
    console.log('transformedSerials: ', transformedSerials);

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
  var chartDiv = document.getElementById("chart_row");
  chartDiv.innerHTML = "";
}


window.onload = (event) => {
  resetState();
  fetchConfig();
};
