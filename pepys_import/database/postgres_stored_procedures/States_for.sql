--DROPING EXISTING PEPYS.STATES_FOR FUNCTION
DROP FUNCTION IF EXISTS PEPYS.STATES_FOR;

--CREATING PEPYS.STATES_FOR FUNCTION
CREATE FUNCTION PEPYS.STATES_FOR(
    INP_START_TIME TEXT,
    INP_END_TIME TEXT,
    INP_LOCATION TEXT,
    INP_SENSOR_SOURCE_MAP TEXT,
    INP_PAGE_NO INTEGER DEFAULT -1,
    INP_PAGE_SIZE INTEGER DEFAULT -1)
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
	speed double precision,
	reference varchar(150))
AS
$$
--Name: States_For
--Version: v0.18
	 with
	ui_filter_input as
		(select
				inp_start_time start_time, --Input should be same as for Phase 1
				inp_end_time end_time,  --Input should be same as for Phase 1
				inp_location "location", --Input should be same as for Phase 1
				inp_sensor_source_map::text source_map, --Input for sensor and source map
				inp_page_no::integer page_no, --Pagination input. Page No For ex. if there are 1000 records paginated into pages of 100 records each, 1 here will return the first page or first 100 records
				inp_page_size::integer page_size --Pagination input - No. of records per page
		),
		processed_ui_filter_values as
		(select
				case when (trim(ui_input.start_time)='' OR ui_input.start_time is null) then '1000-01-01 00:00:00.000000'::timestamp else to_timestamp(ui_input.start_time, 'YYYY-MM-DD HH24:MI:SS.US') end as start_time,
				case when (trim(ui_input.end_time)='' OR ui_input.end_time is null) then '9999-12-12 23:59:59.000000'::timestamp else to_timestamp(ui_input.end_time, 'YYYY-MM-DD HH24:MI:SS.US') end as end_time,
				case when (trim(ui_input.location)='' OR ui_input.location is null) then null else ST_GeomFromText(ui_input.location) end as location
			from
					ui_filter_input as ui_input
		),
		source_map_values as
		(
			select
				json_each(source_map::json) psmap
			from
				ui_filter_input
		),
		sensor_source_maps as
		(
			select
				(psmap).key::uuid sensor_id,
				json_array_elements_text((psmap).value)::uuid source_id
			from
				source_map_values
		),
		selected_sensors as
		(select
			sensor_id,
			name,
			host
		from
			pepys."Sensors" sen
		where
			((select source_map from ui_filter_input) is null OR sen.sensor_id in (select sensor_id from sensor_source_maps))
		),
		filtered_sensors as
		(select
			sen.sensor_id,
			sen.name sensor_name,
			plat.name platform_name,
			platty.name platformtype_name,
			nat.name nationality_name
		from
			selected_sensors as sen inner join
			pepys."Platforms" as plat on sen.host=plat.platform_id inner join
			pepys."PlatformTypes" as platty on plat.platform_type_id = platty.platform_type_id inner join
			pepys."Nationalities" as nat on plat.nationality_id = nat.nationality_id
		),
		filtered_datafiles as
		(select
			datafile_id,
			reference
		from
			pepys."Datafiles" dat
		where
			--Source criteria from the UI
			((select source_map from ui_filter_input) is null OR dat.datafile_id in (select source_id from sensor_source_maps))
		),
		filtered_states as
		(select
			st.state_id,
			st.time,
			st.location,
			st.elevation,
			st.heading,
			st.course,
			st.speed,
			st.source_id,
			st.sensor_id
		from
			pepys."States" st
		where
			--Start and End Time criteria from the UI
			tsrange((select start_time::timestamp from processed_ui_filter_values), (select end_time::timestamp from processed_ui_filter_values), '[]') @> st.time AND
			--Spatial criteria from the UI
			((select location from processed_ui_filter_values) is null OR ST_Contains((select location from processed_ui_filter_values),st.location)) AND
			((select source_map from ui_filter_input) is null OR (st.source_id, st.sensor_id) in (select source_id, sensor_id from sensor_source_maps))
		),
		filtered_limits as
		(select
			case when (ui_input.page_no = -1 OR ui_input.page_size = -1) then 1 else ui_input.page_no end as page_no,
			case when (ui_input.page_no = -1 OR ui_input.page_size = -1) then (select count(1) from filtered_states) else ui_input.page_size end as page_size
		from
			ui_filter_input as ui_input
		)
	select
		filtered_states.state_id,
		filtered_states.time,
		filtered_sensors.sensor_name,
		filtered_sensors.platform_name,
		filtered_sensors.platformtype_name,
		filtered_sensors.nationality_name,
		filtered_states.location,
		filtered_states.elevation,
		filtered_states.heading,
		filtered_states.course,
		filtered_states.speed,
		filtered_datafiles.reference
	from
		filtered_states inner join
		filtered_datafiles on filtered_states.source_id=filtered_datafiles.datafile_id inner join
		filtered_sensors on filtered_states.sensor_id = filtered_sensors.sensor_id
	--Sort clause for pagination
	order by
		filtered_states.state_id asc
	limit (select page_size from filtered_limits)
	offset (select page_size*(page_no -1) from filtered_limits);
$$
LANGUAGE SQL;
