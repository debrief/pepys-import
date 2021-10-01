# pylint: disable=duplicate-string-formatting-argument
"""
    The following describes:

        A. LOGIC USED IN "dashboard_stats.sql" QUERY TO DETERMINE COVERAGE AND GAPS

        B. HOW THIS TEST CASE VALIDATES THE ABOVE LOGIC

    A. LOGIC USED IN "dashboard_stats.sql" QUERY TO DETERMINE COVERAGE AND GAPS

        Requirement is to calculate *coverage* and *gaps* in a given period for a platform.

        *gap* is any duration, which exceeds a predefined value called gap_seconds, between
        two adjacent (when sorted using time) records in pepys."States" table for that
        platform within the requested period

        *coverage* are sections that are not *gaps* within the requested period for that platform

        Based on the above definitions, we consider the following values to calculate *gap*/*coverage*

        a) SERIAL_START_TIME and SERIAL_END_TIME: The duration for which *coverage* measurements are to
            be calculated for a given platform
        b) GAP_SECONDS: The predifned value (gap_seconds) considered to determine if duration is a *gap*
            or *coverage*

        The  query uses a layered approach to calculate *gaps* individually under all possible scenario
        and then invert them to find *coverage*

        The query is formed by the following CTEs (Common Table Expression)/Subqueries grouped under these 5 heads,
        the names of which are self-descriptive.

        <<INPUT PARSING CTEs>>
        serial_participants_input_json
        range_types
        serial_participants_json
        participating_platforms

        <<DATA FETCHING CTEs>>
        sensors_involved
        states_involved

        <<GAP DETERMINATION CTEs>>
        state_time_rankings
        participation_sans_activity
        inner_gaps
        edge_cases
        gaps_at_serial_start
        gaps_at_serial_end
        consolidated_gaps

        <<COVERAGE DETERMINATION CTEs>>
        consolidated_gap_ranks
        participation_sans_gap
        act_with_same_part_and_gap_start
        act_with_same_part_and_gap_end
        inner_coverage
        coverage_at_serial_start
        coverage_at_serial_end
        consolidated_coverage
        consolidated_coverage_with_created

        <<STAT CONSOLIDATION CTE>>
        consolidated_stats

        To determine adjacency, the pepys."States" records are sorted based on time and numbered
        over serial_id, platform_id, and ser_idx in state_time_rankings CTE.
        Before determining adjacency, duplicate "States" are merged into single "State" (as multiple sensors
        might generate the same set of records). The merge is accomplished by gouping the records
        using all the items that are being selected from this CTE. The "created_date" alone is calculated
        as the most recent/max of the entries belonging to the merged group

        The following exhaustive cases are considered for *gap* determination

        participation_sans_activity:
           This indicates a period of exercise where there are no corresponding pepys."States" records.
           In this case, the entire period is marked as *gap*

        inner_gaps:
            This fetches all normally occuring *gaps* between two adjacent pepys."States".time records
            within the SERIAL_START_TIME and SERIAL_END_TIME

        gaps_at_serial_start:
            This identifies *gaps* between SERIAL_START_TIME and the first pepys."States" record
            for that platform and serial_id

        gaps_at_serial_end:
            This identifies *gaps* between SERIAL_END_TIME and the last pepys."States" record
            for that platform and serial_id

        consolidated_gaps:
            This consolidates all the *gaps* identified in the above gap CTEs

        The following exhaustive scenarios are considered for *coverage* determination

        participation_sans_gap:
            This identifies all serial participations without any *gaps* and marks the entire
            duration as *coverage*

        act_with_same_part_and_gap_start:
            These are edge cases where the SERIAL_START_TIME and the first pepys."States" record
            are the same, and the next pepys."States".time record is at a *gap* from the first.
            This CTEs consolidates all such periods and marks their SERIAL_START_TIME as a
            *coverage* record of duration 0.

        act_with_same_part_and_gap_end:
            These are edge cases where the SERIAL_END_TIME and the last pepys."States" record
            are the same, and the subsequent pepys."States".time record is at a *gap* from the last.
            This CTEs consolidates all such periods and marks their SERIAL_END_TIME as a
            *coverage* record of duration 0.

        inner_coverage:
            This fetches all normally occuring *coverage* between two adjacent *gap* period
            within the SERIAL_START_TIME and SERIAL_END_TIME. The end time of the first *gap*
            and the start time of the next *gap* is marked as *coverage*. *coverage* records can
            also be of duration 0, i.e. the two *gaps* are separated by a singe pepys."State"
            record.

        coverage_at_serial_start:
            This identifies *coverage* between SERIAL_START_TIME and the first pepys."States" record
            for that platform and serial_id

        coverage_at_serial_end:
            This identifies *coverage* between SERIAL_END_TIME and the last pepys."States" record
            for that platform and serial_id

        consolidated_coverage:
            This consolidates all the *coverage* identified in the above gap CTEs

        consolidated_coverage_with_created:
            This CTE just determines and adds the time of the most recent "States" added to all "Coverage"
            determined by the consolidated_coverage CTE. It does so by comparing consolidated_coverage CTE
            with state_time_rankings CTE




        How was it ensured that the list of scenarios described above was exhaustive?

        For *gap*/*coverage* calculation, the following items are considered.(as described previously)
        a) SERIAL_START_TIME and SERIAL_END_TIME
        b) GAP_SECONDS

        Let's look at all possible scenarios for any platform one by one.

        #Scenarios with no records
        Scenario [SC1]: No pepys."States" record between SERIAL_START_TIME and SERIAL_END_TIME
            In this scenario, the entire duration between SERIAL_START_TIME and SERIAL_END_TIME
            is to be marked as *gap*. This is handled by participation_sans_activity CTE.
        CTE: participation_sans_activity

        #Scenarios with exactly one record
        Scenario [SC2]: One pepys."States" record exists anywhere between SERIAL_START_TIME and
        SERIAL_START_TIME (both inclusive)
            In this scenario, the pepys."States" record could be
                a) In the same point as SERIAL_START_TIME
                b) In the same point as SERIAL_END_TIME
                c) At a point greater than SERIAL_START_TIME and lesser
                     than SERIAL_END_TIME such that the durations between
                     SERIAL_START_TIME and pepys."States".time, and
                     pepys."States".time and SERIAL_END_TIME are
                     i)   both lesser than GAP_SECONDS
                     ii)  lesser, and greater, respectively, than GAP_SECONDS
                     iii) greater, and lesser, respectively, than GAP_SECONDS
                     iv)  both greater than GAP_SECONDS
            Since there's only one pepys."States" record, there'll not be any *gap* between
            pepys."States" records.
            For a) and b), the entire duration will be marked as a *gap* by participation_sans_activity
            CTE, and the 0 duration coverage will be provided by act_with_same_part_and_gap_start and
            act_with_same_part_and_gap_end CTEs, respectively.
            For c), the *gap* or *coverage* sections are determined, respectively, by
                i)   participation_sans_gap
                ii)  coverage_at_serial_start, gaps_at_serial_end
                iii) gaps_at_serial_start, coverage_at_serial_end
                iv)  gaps_at_serial_start, gaps_at_serial_end
        CTE: participation_sans_activity, act_with_same_part_and_gap_start, act_with_same_part_and_gap_end,
            gaps_at_serial_start, gaps_at_serial_end, coverage_at_serial_start, coverage_at_serial_end, and
            participation_sans_gap

        #Scenarios with 2 or more record
        Scenario [SC3]: Two or more pepys."States" record exists anywhere between SERIAL_START_TIME and
        SERIAL_START_TIME (both inclusive and there are no overlaps)

            Since there're 2 or more pepys."States" records, adjacent records can be measured for *gap*.

            If there are *gap*,these will be detected by inner_gaps CTE, and subsequently inverted by inner_coverage CTE
            to identify *coverage* between the SERIAL_START_TIME and SERIAL_END_TIME for this platform.

            The records nearest to the SERIAL_START_TIME and SERIAL_END_TIME are also checked by
            gaps_at_serial_start, gaps_at_serial_end

            After all *gap* are identified, the records nearest to the SERIAL_START_TIME and
            SERIAL_END_TIME are also checked by
            act_with_same_part_and_gap_start, act_with_same_part_and_gap_end, inner_coverage,
            coverage_at_serial_start, coverage_at_serial_end

            If there are no *gap*, participation_sans_gap CTE will mark the entire period as *coverage*

        CTE: inner_gaps, inner_coverage, gaps_at_serial_start, gaps_at_serial_end, act_with_same_part_and_gap_start,
        act_with_same_part_and_gap_end, inner_coverage, coverage_at_serial_start, coverage_at_serial_end



    B. HOW THIS TEST CASE VALIDATES THE ABOVE LOGIC

        This test case validates the mentioned logic by simulating the three scenarios mentioned above.

"""
import json
import os
import unittest
from itertools import zip_longest

import psycopg2
import pytest
import testing.postgresql

import paths

SQL_FILE_LOCATION = os.path.join(
    paths.PEPYS_IMPORT_DIRECTORY, "database", "postgres_stored_procedures", "dashboard_stats.sql"
)

META_SQL_FILE_LOCATION = os.path.join(
    paths.PEPYS_IMPORT_DIRECTORY, "database", "postgres_stored_procedures", "dashboard_metadata.sql"
)

SOME_UUID = "54f6d015-8adf-47f4-bf02-33e06fbe0725"
SOME_UUID2 = "54f6d015-8bdf-47f4-bf02-33e06fbe0725"
TIMELIST = ["09:00:00", "17:00:00", "17:01:00", "17:02:00"]
DATEVAL = "2020-12-12 "
CREATED = "2020-12-12 08:30:00"
GAP_SECONDS = 150


@pytest.mark.postgres
class TestDashboardStatsQuery(unittest.TestCase):
    """
    This class is to unit test the business logic implemented in dashboard_stats query.
    This class also tests few features in dashboard_metadata query.
    """

    def setUp(self):
        self.postgresql = testing.postgresql.Postgresql()

    def tearDown(self):
        self.postgresql.stop()

    def test_query_logic(self):
        with psycopg2.connect(**self.postgresql.dsn()) as conn:
            cursor = conn.cursor()
            populate_data(cursor, TIMELIST)
            populate_additional_data(cursor)

            # Sample Tests
            rows = fetchrows(cursor, "12:12:12", "15:12:12")
            assert validateStartTimes(rows, ["G"], ["12:12:12"])
            assert validateEndTimes(rows, ["G"], ["15:12:12"])
            rows = fetchrows(cursor, "08:00:00", "15:12:12")
            assert validateStartTimes(rows, ["G", "C", "G"], ["08:00:00", "09:00:00", "09:00:00"])
            assert validateEndTimes(rows, ["G", "C", "G"], ["09:00:00", "09:00:00", "15:12:12"])

            # Tests for scenario 1[SC1]: No records between SERIAL_START_TIME and SERIAL_END_TIME
            rows = fetchrows(cursor, "06:00:00", "08:00:00")
            assert validateStartTimes(rows, ["G"], ["06:00:00"])
            assert validateEndTimes(rows, ["G"], ["08:00:00"])

            # Tests for scenario 2[SC2]: One record between SERIAL_START_TIME and SERIAL_END_TIME
            # a) In the same point as SERIAL_START_TIME
            rows = fetchrows(cursor, "09:00:00", "10:00:00")
            assert validateStartTimes(rows, ["C", "G"], ["09:00:00", "09:00:00"])
            assert validateEndTimes(rows, ["C", "G"], ["09:00:00", "10:00:00"])
            rows = fetchrows(cursor, "09:00:00", "09:02:00")
            assert validateStartTimes(rows, ["C"], ["09:00:00"])
            assert validateEndTimes(rows, ["C"], ["09:02:00"])
            # b) In the same point as SERIAL_END_TIME
            rows = fetchrows(cursor, "08:00:00", "09:00:00")
            assert validateStartTimes(rows, ["G", "C"], ["08:00:00", "09:00:00"])
            assert validateEndTimes(rows, ["G", "C"], ["09:00:00", "09:00:00"])
            rows = fetchrows(cursor, "08:58:00", "09:00:00")
            assert validateStartTimes(rows, ["C"], ["08:58:00"])
            assert validateEndTimes(rows, ["C"], ["09:00:00"])
            # c) At a point greater than SERIAL_START_TIME and lesser
            # than SERIAL_END_TIME such that the durations between
            # SERIAL_START_TIME and pepys."States".time, and
            # pepys."States".time and SERIAL_END_TIME are
            # i)   both lesser than GAP_SECONDS
            rows = fetchrows(cursor, "08:58:00", "09:01:00")
            assert validateStartTimes(rows, ["C"], ["08:58:00"])
            assert validateEndTimes(rows, ["C"], ["09:01:00"])
            # ii)  lesser, and greater, respectively, than GAP_SECONDS
            rows = fetchrows(cursor, "08:58:00", "09:09:00")
            assert validateStartTimes(rows, ["C", "G"], ["08:58:00", "09:00:00"])
            assert validateEndTimes(rows, ["C", "G"], ["09:00:00", "09:09:00"])
            # iii) greater, and lesser, respectively, than GAP_SECONDS
            rows = fetchrows(cursor, "08:55:00", "09:01:00")
            assert validateStartTimes(rows, ["G", "C"], ["08:55:00", "09:00:00"])
            assert validateEndTimes(rows, ["G", "C"], ["09:00:00", "09:01:00"])
            # iv)  both greater than GAP_SECONDS
            rows = fetchrows(cursor, "08:55:00", "09:05:00")
            assert validateStartTimes(rows, ["G", "C", "G"], ["08:55:00", "09:00:00", "09:00:00"])
            assert validateEndTimes(rows, ["G", "C", "G"], ["09:00:00", "09:00:00", "09:05:00"])
            # Tests for Scenario 3 [SC3] with 2 or more record
            rows = fetchrows(cursor, "16:55:00", "17:05:00")
            assert validateStartTimes(rows, ["G", "C", "G"], ["16:55:00", "17:00:00", "17:02:00"])
            assert validateEndTimes(rows, ["G", "C", "G"], ["17:00:00", "17:02:00", "17:05:00"])
            rows = fetchrows(cursor, "17:00:00", "17:05:00")
            assert validateStartTimes(rows, ["C", "G"], ["17:00:00", "17:02:00"])
            assert validateEndTimes(rows, ["C", "G"], ["17:02:00", "17:05:00"])
            rows = fetchrows(cursor, "17:01:00", "17:05:00")
            assert validateStartTimes(rows, ["C", "G"], ["17:01:00", "17:02:00"])
            assert validateEndTimes(rows, ["C", "G"], ["17:02:00", "17:05:00"])

            # Tests for dashboard_metadata function
            rows = fetchrowsMeta(cursor, DATEVAL + "08:00:00", DATEVAL + "20:00:00")
            assert validateForIncludeInTimeline(rows)

            # Tests for #1019 (https://github.com/debrief/pepys-import/issues/1019)
            # There should be only one gap for SC1 as defined above
            # Tests for scenario 1[SC1]: No records between SERIAL_START_TIME and SERIAL_END_TIME
            rows = fetchrows(cursor, "06:00:00", "08:00:00")
            # The following asserts would fail without the fix
            assert len(rows) == 1
            assert validateStartTimes(rows, ["G"], ["06:00:00"])
            assert validateEndTimes(rows, ["G"], ["08:00:00"])


class FilterInputJSON:
    pass


class FilterEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


def get_data(listPlatformRanges):
    return FilterEncoder().encode(listPlatformRanges)


def get_query(funcName):
    # security checks suppressed on next line since it isn't processing user data
    return "select * from pepys.dashboard_" + funcName + "(%s, %s)"  # nosec


def populate_data(cursor, TIMELIST):
    cursor.execute("create schema pepys")
    cursor.execute('create table pepys."Sensors"(host uuid, sensor_id uuid)')
    cursor.execute(
        'create table pepys."States"(sensor_id uuid, time timestamp, created_date timestamp )'
    )
    cursor.execute(
        'create table pepys."Serials"(serial_id uuid, serial_number text, exercise varchar(150), '
        'include_in_timeline bool, start timestamp, "end" timestamp)'
    )
    cursor.execute(
        'create table pepys."SerialParticipants"(serial_id uuid, wargame_participant_id uuid, '
        'force_type_id uuid, start timestamp, "end" timestamp)'
    )
    cursor.execute(
        'create table pepys."WargameParticipants"(wargame_participant_id uuid, platform_id uuid)'
    )
    cursor.execute(
        'create table pepys."Platforms"(platform_id uuid, platform_type_id uuid, quadgraph varchar(4), name varchar(150))'
    )
    cursor.execute(
        'create table pepys."PlatformTypes"(platform_type_id uuid, default_data_interval_secs int4, name varchar(150))'
    )
    cursor.execute(
        'create table pepys."ForceTypes"(force_type_id uuid, name varchar(150), color varchar(10))'
    )

    cursor.execute(
        """insert into pepys."Sensors" values('{}', '{}')""".format(SOME_UUID, SOME_UUID)
    )
    cursor.execute(
        """insert into pepys."Serials" values('{}', '{}', '{}', {},
            to_timestamp('{}','YYYY-MM-DD HH24:MI:SS'), to_timestamp('{}',
            'YYYY-MM-DD HH24:MI:SS') + interval '12 hours')""".format(
            SOME_UUID, "J052010", "EXERCISE", "true", CREATED, CREATED
        )
    )
    for time in TIMELIST:
        cursor.execute(
            """insert into pepys."States" values('{}', '{}{}', '{}')""".format(
                SOME_UUID, DATEVAL, time, CREATED
            )
        )

    cursor.execute(
        """insert into pepys."SerialParticipants" values('{}', '{}', '{}',
            to_timestamp('{}','YYYY-MM-DD HH24:MI:SS'), to_timestamp('{}',
            'YYYY-MM-DD HH24:MI:SS') + interval '12 hours')""".format(
            SOME_UUID, SOME_UUID, SOME_UUID, CREATED, CREATED
        )
    )
    cursor.execute(
        """insert into pepys."WargameParticipants" values('{}', '{}')""".format(
            SOME_UUID, SOME_UUID
        )
    )
    cursor.execute(
        """insert into pepys."Platforms" values('{}', '{}', '{}', '{}')""".format(
            SOME_UUID, SOME_UUID, "ABCD", "PlatName"
        )
    )
    cursor.execute(
        """insert into pepys."PlatformTypes" values('{}', {}, '{}')""".format(
            SOME_UUID, 30, "PtypeName"
        )
    )
    cursor.execute(
        """insert into pepys."ForceTypes" values('{}', '{}', '{}')""".format(
            SOME_UUID, "ForceTypeName", "RED"
        )
    )

    with open(SQL_FILE_LOCATION, "r") as statssqlfile:
        cursor.execute(statssqlfile.read())

    with open(META_SQL_FILE_LOCATION, "r") as metasqlfile:
        cursor.execute(metasqlfile.read())


def populate_additional_data(cursor):
    cursor.execute(
        """insert into pepys."Sensors" values('{}', '{}')""".format(SOME_UUID, SOME_UUID2)
    )


def fetchrows(cursor, start, end):
    cursor.execute(get_query("stats"), get_test_case_data(start, end))
    return cursor.fetchall()


def get_test_case_data(start, end):
    fij = FilterInputJSON()
    fij.serial_id = fij.platform_id = SOME_UUID
    fij.start = DATEVAL + start
    fij.end = DATEVAL + end
    fij.gap_seconds = GAP_SECONDS
    return (
        get_data([fij]),
        '["C","G"]',
    )


def fetchrowsMeta(cursor, start, end):
    cursor.execute(get_query("metadata"), (start, end))
    return cursor.fetchall()


def validateStartTimes(rows, rangeTypes, startTimes):
    for (row, ranget, startt) in zip_longest(rows, rangeTypes, startTimes):
        (rangetype, starttime, endtime, created_date, platid, serialid) = row
        if rangetype != ranget or startt != starttime.strftime("%H:%M:%S"):
            print(row, ranget, startt)
            return False
    return True


def validateEndTimes(rows, rangeTypes, endTimes):
    for (row, ranget, endt) in zip_longest(rows, rangeTypes, endTimes):
        # pylint: disable=unused-variable
        (rangetype, starttime, endtime, created_date, platid, serialid) = row
        if rangetype != ranget or endt != endtime.strftime("%H:%M:%S"):
            print(row, ranget, endt)
            return False
    return True


def validateForIncludeInTimeline(rows):
    for row in rows:
        # pylint: disable=unused-variable
        (
            recordType,
            includeInTimeline,
            serialid,
            pid,
            pname,
            exercise,
            ptname,
            start,
            end,
            gap,
            intervalMissing,
            ftname,
            ftcolor,
        ) = row
        if recordType == "SERIALS":
            return includeInTimeline
    return False


if __name__ == "__main__":
    unittest.main()
