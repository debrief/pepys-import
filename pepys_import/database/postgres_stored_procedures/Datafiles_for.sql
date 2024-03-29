--DROPING EXISTING PEPYS.DATAFILES_FOR FUNCTION
DROP FUNCTION IF EXISTS PEPYS.DATAFILES_FOR;

--CREATING PEPYS.DATAFILES_FOR FUNCTION
CREATE FUNCTION PEPYS.DATAFILES_FOR(
    INP_START_TIME TEXT,
    INP_END_TIME TEXT,
    INP_LOCATION TEXT,
    INP_DATA_TYPES TEXT[],
    INP_COMMENT_SEARCH_STRING TEXT)
RETURNS TABLE (
    PLATFORM_NAME varchar(150),
    PLATFORM_ID UUID,
    DATATYPE text,
    SENSOR_NAME varchar(150),
    SENSOR_ID UUID,
    REFERENCE varchar(150),
    DATAFILE_ID UUID,
    AGG_COUNT BIGINT)
AS
$$
--Name: Datafiles_For 
--Version: v0.16
    with
	ui_filter_input as
		(select
				INP_START_TIME START_TIME,
				INP_END_TIME END_TIME,
				INP_LOCATION "location",
				INP_DATA_TYPES::text[] DATA_TYPES,
				INP_COMMENT_SEARCH_STRING COMMENT_SEARCH_STRING
		),
		processed_ui_filter_values as
		(select
				case when (trim(ui_input.start_time)='' OR ui_input.start_time is null) then '1000-01-01 00:00:00.000000'::timestamp else to_timestamp(ui_input.start_time, 'YYYY-MM-DD HH24:MI:SS.US') end as start_time,
				case when (trim(ui_input.end_time)='' OR ui_input.end_time is null) then '9999-12-12 23:59:59.000000'::timestamp else to_timestamp(ui_input.end_time, 'YYYY-MM-DD HH24:MI:SS.US') end as end_time,
				case when (trim(ui_input.location)='' OR ui_input.location is null) then null else ST_GeomFromText(ui_input.location) end as location,
				case when (coalesce(array_length(ui_input.data_types,1),0)::int = 0) then string_to_array('NO_DATA_TYPE_SELECTED',',') else ui_input.data_types end as data_types,
				case when (trim(ui_input.comment_search_string)='' OR ui_input.comment_search_string is null) then null::varchar else '%'||upper(ui_input.comment_search_string)||'%' end as comment_search_string
			from
					ui_filter_input as ui_input
			),
	state_aggregation_data as
		(select
				States.sensor_id, States.source_id, count(1) as state_agg_count
			from pepys."States" as States
			WHERE
				--Data Type criteria from the UI
				array_position((select data_types from processed_ui_filter_values),'STATES') > 0 AND
				--Start and End Time criteria from the UI
				tsrange((select start_time::timestamp from processed_ui_filter_values), (select end_time::timestamp from processed_ui_filter_values), '[]') @> States.time AND
				--Spatial criteria from the UI
				((select location from processed_ui_filter_values) is null OR ST_Contains((select location from processed_ui_filter_values),States.location))
				group by States.sensor_id, States.source_id
		),
	state_measurement_data AS
		(SELECT
				Platforms.name as "PLATFORM_NAME", Platforms.platform_id, 'STATES' AS datatype, Sensors.name as "SENSOR_NAME", Sensors.sensor_id, Datafiles.reference, Datafiles.datafile_id, sad.state_agg_count
			from
				state_aggregation_data as sad inner join
				pepys."Sensors" as Sensors on Sensors.sensor_id = sad.sensor_id inner join
				pepys."Platforms" as Platforms on Platforms.platform_id=Sensors.host INNER JOIN
				pepys."Datafiles" AS Datafiles on Datafiles.datafile_id=sad.source_id
		),
	contact_aggregation_data as
		(select
				Contacts.sensor_id, Contacts.source_id, count(1) as contact_agg_count
			from pepys."Contacts" as Contacts
			WHERE
				--Data Type criteria from the UI
				array_position((select data_types from processed_ui_filter_values),'CONTACTS') > 0 AND
				--Start and End Time criteria from the UI
				tsrange((select start_time::timestamp from processed_ui_filter_values), (select end_time::timestamp from processed_ui_filter_values), '[]') @> Contacts.time AND
				--Spatial criteria from the UI
				((select location from processed_ui_filter_values) is null OR ST_Contains((select location from processed_ui_filter_values),Contacts.location))
				group by Contacts.sensor_id, Contacts.source_id
		),
	contact_measurement_data AS
		(SELECT
				Platforms.name as "PLATFORM_NAME", Platforms.platform_id, 'CONTACTS' AS datatype, Sensors.name as "SENSOR_NAME", Sensors.sensor_id, Datafiles.reference, Datafiles.datafile_id, cad.contact_agg_count
			from
				contact_aggregation_data as cad inner join
				pepys."Sensors" as Sensors on Sensors.sensor_id = cad.sensor_id inner join
				pepys."Platforms" as Platforms on Platforms.platform_id=Sensors.host INNER JOIN
				pepys."Datafiles" AS Datafiles on Datafiles.datafile_id=cad.source_id
		),
	comment_aggregation_data as
		(select
				Comments.platform_id, Comments.source_id, count(1) as comment_agg_count
			from pepys."Comments" as Comments
			WHERE
				--Data Type criteria from the UI
				array_position((select data_types from processed_ui_filter_values),'COMMENTS') > 0 AND
				--Start and End Time criteria from the UI
				tsrange((select start_time::timestamp from processed_ui_filter_values), (select end_time::timestamp from processed_ui_filter_values), '[]') @> Comments.time AND
				--Comment search criteria from the UI
				((select comment_search_string from processed_ui_filter_values) is null OR upper(Comments.content) like (select comment_search_string from processed_ui_filter_values))
				group by Comments.platform_id, Comments.source_id
		),
	comment_measurement_data AS
		(SELECT
				Platforms.name as "PLATFORM_NAME", Platforms.platform_id, 'COMMENTS' AS datatype, null as "SENSOR_NAME", null::uuid, Datafiles.reference, Datafiles.datafile_id, cad.comment_agg_count
			from
				comment_aggregation_data as cad inner join
				pepys."Platforms" as Platforms on Platforms.platform_id=cad.platform_id INNER JOIN
				pepys."Datafiles" AS Datafiles on Datafiles.datafile_id=cad.source_id
		),
	consolidated_measurement_data as
		(
				select * from state_measurement_data
				union all
				select * from contact_measurement_data
				union all
				select * from comment_measurement_data
		)
	SELECT * FROM consolidated_measurement_data cmd
	--Sorting based on Platform Name, Data Type, Sensor Name, and  Datafile Reference
	order by
		cmd."PLATFORM_NAME" ASC,
		cmd.datatype ASC,
		cmd."SENSOR_NAME" ASC,
		cmd.reference ASC;
$$
LANGUAGE SQL;
