--DROPING EXISTING PEPYS.DETAILED_STATES_FOR FUNCTION
DROP FUNCTION IF EXISTS PEPYS.DETAILED_STATES_FOR;

--CREATING PEPYS.STATES_FOR FUNCTION
CREATE FUNCTION PEPYS.DETAILED_STATES_FOR(
    INP_START_TIME TEXT,
    INP_END_TIME TEXT,
    INP_BOUNDS TEXT,
    INP_SENSOR_ID TEXT[],
    INP_SOURCE_ID TEXT[],
    INP_PLATFORM_ID TEXT[],
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
	reference varchar(150),
	north double precision,
	east double precision,
	down double precision,
	x double precision,
	y double precision,
	z double precision,
	phi double precision,
	theta double precision,
	psi double precision,
	north_dot double precision,
	east_dot double precision,
	down_dot double precision,
	x_dot double precision,
	y_dot double precision,
	z_dot double precision,
	phi_dot double precision,
	theta_dot double precision,
	psi_dot double precision,
	north_dot_dot double precision,
	east_dot_dot double precision,
	down_dot_dot double precision,
	x_dot_dot double precision,
	y_dot_dot double precision,
	z_dot_dot double precision,
	phi_dot_dot double precision,
	theta_dot_dot double precision,
	psi_dot_dot double precision
)
AS
$$
--Name: Detailed_States_For
--Version: v0.18
	 with
		ui_filter_input as
		(select
				inp_start_time start_time, --Input should be same as for Phase 1
				inp_end_time end_time,  --Input should be same as for Phase 1
				inp_bounds bounds, --Input should be same as for Phase 1 
				inp_sensor_id::text[] sensor_id,  --Input from Phase 2 of import, can be set as null: null as sensor_id
				inp_source_id::text[] source_id,  --Input from Phase 2 of import, can be set as null: null as source_id
				inp_platform_id::text[] platform_id,  --Input from Phase 2 of import, can be set as null: null as platform_id
				--null as platform_id,  --Example on how to provide null
				inp_page_no::integer page_no, --Pagination input. Page No For ex. if there are 1000 records paginated into pages of 100 records each, 1 here will return the first page or first 100 records
				inp_page_size::integer page_size --Pagination input - No. of records per page
		),
		processed_ui_filter_values as
		(select
				case when (trim(ui_input.start_time)='' OR ui_input.start_time is null) then '1000-01-01 00:00:00.000000'::timestamp else to_timestamp(ui_input.start_time, 'YYYY-MM-DD HH24:MI:SS.US') end as start_time,
				case when (trim(ui_input.end_time)='' OR ui_input.end_time is null) then '9999-12-12 23:59:59.000000'::timestamp else to_timestamp(ui_input.end_time, 'YYYY-MM-DD HH24:MI:SS.US') end as end_time,
				case when (trim(ui_input.bounds)='' OR ui_input.bounds is null) then null else ST_GeomFromText(ui_input.bounds) end as bounds,
				case when (coalesce(array_length(ui_input.sensor_id,1),0)::int = 0) then null else ui_input.sensor_id end as sensor_id,
				case when (coalesce(array_length(ui_input.source_id,1),0)::int = 0) then null else ui_input.source_id end as source_id,
				case when (coalesce(array_length(ui_input.platform_id,1),0)::int = 0) then null else ui_input.platform_id end as platform_id
			from
					ui_filter_input as ui_input
		),
		selected_sensors as
		(select
			sensor_id,
			name,
			host
		from
			pepys."Sensors" sen
		where
			--Platform criteria from the UI
			((select platform_id from processed_ui_filter_values) is null OR sen.host in (select unnest(platform_id::uuid[]) from processed_ui_filter_values)) AND
			--Sensor criteria from the UI
			((select sensor_id from processed_ui_filter_values) is null OR sen.sensor_id in (select unnest(sensor_id::uuid[]) from processed_ui_filter_values))
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
			((select source_id from processed_ui_filter_values) is null OR dat.datafile_id in (select unnest(source_id::uuid[]) from processed_ui_filter_values))
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
			st.sensor_id,
			std.north,
			std.east,
			std.down,
			std.x,
			std.y,
			std.z,
			std.phi,
			std.theta,
			std.psi,
			std.north_dot,
			std.east_dot,
			std.down_dot,
			std.x_dot,
			std.y_dot,
			std.z_dot,
			std.phi_dot,
			std.theta_dot,
			std.psi_dot,
			std.north_dot_dot,
			std.east_dot_dot,
			std.down_dot_dot,
			std.x_dot_dot,
			std.y_dot_dot,
			std.z_dot_dot,
			std.phi_dot_dot,
			std.theta_dot_dot,
			std.psi_dot_dot
		from
				pepys."States" st
			left join
				pepys."States_Detailed" std
			on st.state_id = std.state_id
		where
			--Start and End Time criteria from the UI
			tsrange((select start_time::timestamp from processed_ui_filter_values), (select end_time::timestamp from processed_ui_filter_values), '[]') @> st.time AND
			--Spatial criteria from the UI
			((select bounds from processed_ui_filter_values) is null OR ST_Contains((select bounds from processed_ui_filter_values),st.location)) AND
			--Sensor criteria from the UI
			((select sensor_id from processed_ui_filter_values) is null OR st.sensor_id in (select unnest(sensor_id::uuid[]) from processed_ui_filter_values)) AND
			--Source criteria from the UI
			((select source_id from processed_ui_filter_values) is null OR st.source_id in (select unnest(source_id::uuid[]) from processed_ui_filter_values))
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
		filtered_datafiles.reference,
		filtered_states.north,
		filtered_states.east,
		filtered_states.down,
		filtered_states.x,
		filtered_states.y,
		filtered_states.z,
		filtered_states.phi,
		filtered_states.theta,
		filtered_states.psi,
		filtered_states.north_dot,
		filtered_states.east_dot,
		filtered_states.down_dot,
		filtered_states.x_dot,
		filtered_states.y_dot,
		filtered_states.z_dot,
		filtered_states.phi_dot,
		filtered_states.theta_dot,
		filtered_states.psi_dot,
		filtered_states.north_dot_dot,
		filtered_states.east_dot_dot,
		filtered_states.down_dot_dot,
		filtered_states.x_dot_dot,
		filtered_states.y_dot_dot,
		filtered_states.z_dot_dot,
		filtered_states.phi_dot_dot,
		filtered_states.theta_dot_dot,
		filtered_states.psi_dot_dot
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


GRANT EXECUTE ON FUNCTION PEPYS.DETAILED_STATES_FOR TO TRACSTOR_VIEW;
COMMIT;s