--DROPING EXISTING PEPYS.STATES_FOR FUNCTION
DROP FUNCTION IF EXISTS PEPYS.STATES_FOR;

--CREATING PEPYS.STATES_FOR FUNCTION
CREATE FUNCTION PEPYS.STATES_FOR(
    INP_START_TIME TEXT,
    INP_END_TIME TEXT,
    INP_LOCATION TEXT,
    INP_SENSOR_ID TEXT[],
    INP_SOURCE_ID TEXT[],
    INP_PLATFORM_ID TEXT[],
    INP_PAGE_NO INTEGER DEFAULT 1,
    INP_PAGE_SIZE INTEGER DEFAULT 100)
RETURNS TABLE (
	state_id UUID,
	state_time TIMESTAMP WITHOUT TIME ZONE,
	sensor_name varchar(150),
	platform_name varchar(150),
	platformtype_name varchar(150),
	nationality_name varchar(150),
	state_location public.geometry(Point,4326),
	elevation double precision,
	heading double precision,
	course double precision,
	speed double precision)
AS
$$
--Name: States_For 
--Version: v0.15
	 with
	ui_filter_input as
		(select
				inp_start_time start_time, --Input should be same as for Phase 1
				inp_end_time end_time,  --Input should be same as for Phase 1
				inp_location "location", --Input should be same as for Phase 1
				inp_sensor_id::text[] sensor_id,  --Input from Phase 2 of import, can be set as null: null as sensor_id
				inp_source_id::text[] source_id,  --Input from Phase 2 of import, can be set as null: null as source_id
				inp_platform_id::text[] platform_id,  --Input from Phase 2 of import, can be set as null: null as platform_id
				--null as platform_id,  --Example on how to provide null
				inp_page_no page_no, --Pagination input. Page No For ex. if there are 1000 records paginated into pages of 100 records each, 1 here will return the first page or first 100 records
				inp_page_size page_size --Pagination input - No. of records per page
		),
		processed_ui_filter_values as
		(select
				case when (trim(ui_input.start_time)='' OR ui_input.start_time is null) then '1000-01-01 00:00:00.000000'::timestamp else to_timestamp(ui_input.start_time, 'YYYY-MM-DD HH24:MI:SS.US') end as start_time,
				case when (trim(ui_input.end_time)='' OR ui_input.end_time is null) then '9999-12-12 23:59:59.000000'::timestamp else to_timestamp(ui_input.end_time, 'YYYY-MM-DD HH24:MI:SS.US') end as end_time,
				case when (trim(ui_input.location)='' OR ui_input.location is null) then null else ST_GeomFromText(ui_input.location) end as location,
				case when (coalesce(array_length(ui_input.sensor_id,1),0)::int = 0) then null else ui_input.sensor_id end as sensor_id,
				case when (coalesce(array_length(ui_input.source_id,1),0)::int = 0) then null else ui_input.source_id end as source_id,
				case when (coalesce(array_length(ui_input.platform_id,1),0)::int = 0) then null else ui_input.platform_id end as platform_id,
				case when (ui_input.page_no is null OR ui_input.page_no <=0) then 1 else ui_input.page_no end as page_no,
				case when (ui_input.page_size is null OR ui_input.page_size <=0) then 100 else ui_input.page_size end as page_size
			from
					ui_filter_input as ui_input
			)
	select filtered_states.state_id, filtered_states.time, Sensors.name, Platforms.name,
		PlatformTypes.name, Nationalities.name,
		filtered_states.location, filtered_states.elevation, filtered_states.heading, filtered_states.course, filtered_states.speed from
		pepys."States" as filtered_states inner join
		pepys."Sensors" as Sensors on filtered_states.sensor_id = Sensors.sensor_id inner join
		pepys."Platforms" as Platforms on Sensors.host=Platforms.platform_id inner join
		pepys."PlatformTypes" as PlatformTypes on Platforms.platform_type_id = PlatformTypes.platform_type_id inner join
		pepys."Nationalities" as Nationalities on Platforms.nationality_id = Nationalities.nationality_id
			WHERE
				--Start and End Time criteria from the UI
				tsrange((select start_time::timestamp from processed_ui_filter_values), (select end_time::timestamp from processed_ui_filter_values), '[]') @> filtered_states.time AND
				--Spatial criteria from the UI
				((select location from processed_ui_filter_values) is null OR ST_Contains((select location from processed_ui_filter_values),filtered_states.location)) AND
				--Sensor criteria from the UI
				((select sensor_id from processed_ui_filter_values) is null OR filtered_states.sensor_id in (select unnest(sensor_id::uuid[]) from processed_ui_filter_values)) AND
				--Source criteria from the UI
				((select source_id from processed_ui_filter_values) is null OR filtered_states.source_id in (select unnest(source_id::uuid[]) from processed_ui_filter_values)) AND
				--Platform criteria from the UI
				((select platform_id from processed_ui_filter_values) is null OR Sensors.host in (select unnest(platform_id::uuid[]) from processed_ui_filter_values))
				--Sort clause for pagination
				order by filtered_states.state_id asc limit (select page_size from processed_ui_filter_values) offset (select page_size*(page_no -1) from processed_ui_filter_values);  
$$
LANGUAGE SQL;
