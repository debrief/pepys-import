--droping existing pepys.dashboard_stats function
drop function if exists pepys.dashboard_stats;

--creating pepys.dashboard_stats function
create function pepys.dashboard_stats(
	ui_inp_ser_plat_json text,
	ui_inp_range_type text)
returns table (
	resp_range_type text,
	resp_start_time timestamp without time zone,
	resp_end_time timestamp without time zone,
	resp_created timestamp without time zone,
	resp_platform_id uuid,
	resp_serial_id text)
as
$$
begin
	return query
with 
serial_participants_input_json as (
	select 
		ui_inp_ser_plat_json::json spij,
		ui_inp_range_type::json range_types
),
range_types as (
	select
		json_array_elements_text(range_types) range_type
	from
		serial_participants_input_json
),
serial_participants_json as (
	select
		json_array_elements(spij) spj
	from
		serial_participants_input_json
),
participating_platforms as (
	select
		row_number() over () ser_idx,
		(spj->>'serial_id')::uuid serial_id,
		(spj->>'platform_id')::uuid platform_id,
		(spj->>'start')::timestamp serial_participant_start,
		(spj->>'end')::timestamp serial_participant_end,
		(spj->>'gap_seconds')::integer gap_seconds
	from
		serial_participants_json
),
sensors_involved as (
	select
		s.sensor_id,
		pp.platform_id,
		pp.gap_seconds,
		pp.serial_participant_start,
		pp.serial_participant_end,
		pp.serial_id,
		pp.ser_idx
	from
		participating_platforms pp
			inner join
		pepys."Sensors" s
				on s.host = pp.platform_id
),
states_involved as (
	select 
		s.sensor_id,
		s.created_date,
		s.time
	from
		pepys."States" s
	where
		s.time >= (select 
					min(serial_participant_start) 
				from 
					participating_platforms)
			and
		s.time <= (select 
					max(serial_participant_end) 
				from 
					participating_platforms)
			and
		sensor_id in (select 
						sensor_id 
					from 
				sensors_involved)
),
state_time_rankings as (
	select 
		s.time, 
		row_number() over (partition by si.serial_id, si.platform_id, si.ser_idx order by s.time asc) as rowno,
		max(s.created_date) created_date,
		si.platform_id,
		si.gap_seconds,
		si.serial_id,
		si.ser_idx
	from 
		states_involved s
			inner join
		sensors_involved si
				on s.sensor_id = si.sensor_id
				and tsrange(si.serial_participant_start,
							si.serial_participant_end,
							'[]'
							) @> s.time
	group by
		s.time,
		si.platform_id,
		si.gap_seconds,
		si.serial_id,
		si.ser_idx
),
participation_sans_activity as (
	select
		si.serial_participant_start start_time,
		si.serial_participant_end end_time,
		si.platform_id,
		si.serial_id,
		si.ser_idx
	from
		sensors_involved si
	where
		not exists (select 1
					from 
						state_time_rankings s
					where 
						s.serial_id = si.serial_id
							and 
						s.ser_idx = si.ser_idx
							and 
						s.platform_id = si.platform_id
							and
						tsrange(si.serial_participant_start,
								si.serial_participant_end,
								'[]'
								) @> s.time
				)
),
inner_gaps as (
	select
		s.time start_time,
		e.time end_time,
		s.platform_id,
		s.serial_id,
		s.ser_idx
	from
		state_time_rankings s
			inner join
		state_time_rankings e
				on s.platform_id=e.platform_id
				and s.serial_id=e.serial_id
				and s.ser_idx=e.ser_idx
				and s.rowno=e.rowno-1
				and e.time-s.time > s.gap_seconds *  interval '1 second'
),
edge_cases as ( --Identify boundary cases for all platform, serial combination
	select
		str.platform_id,
		str.serial_id,
		str.ser_idx,
		min(str.time) start_time, --Start
		max(str.time) end_time --End
	from
		state_time_rankings str
	group by
		str.platform_id,
		str.serial_id,
		str.ser_idx
),
gaps_at_serial_start as (
	select
		pp.serial_participant_start start_time,
		ec.start_time end_time,
		ec.platform_id,
		ec.serial_id,
		ec.ser_idx
	from
		edge_cases ec
			inner join
		participating_platforms pp
				on ec.platform_id = pp.platform_id
				and ec.serial_id = pp.serial_id
				and ec.ser_idx = pp.ser_idx
				and ec.start_time - pp.serial_participant_start > pp.gap_seconds * interval '1 second'
),
gaps_at_serial_end as (
	select
		ec.end_time start_time,
		pp.serial_participant_end end_time,
		ec.platform_id,
		ec.serial_id,
		ec.ser_idx
	from
		edge_cases ec
			inner join
		participating_platforms pp
				on ec.platform_id = pp.platform_id
				and ec.serial_id = pp.serial_id
				and ec.ser_idx = pp.ser_idx
				and pp.serial_participant_end - ec.end_time > pp.gap_seconds * interval '1 second'
),
consolidated_gaps as (
	select
		start_time,
		end_time,
		platform_id,
		serial_id,
		ser_idx
	from
		inner_gaps
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id,
		ser_idx
	from
		gaps_at_serial_start
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id,
		ser_idx
	from
		gaps_at_serial_end
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id,
		ser_idx
	from
		participation_sans_activity
),
consolidated_gap_ranks as (
	select
		start_time,
		end_time,
		platform_id,
		serial_id,
		ser_idx,
		row_number() over (partition by serial_id, platform_id, ser_idx order by start_time asc) as rowno
	from
		consolidated_gaps
),
participation_sans_gap as (
	select
		si.serial_participant_start start_time,
		si.serial_participant_end end_time,
		si.platform_id,
		si.serial_id,
		si.ser_idx
	from
		sensors_involved si
	where
		not exists (select 1
					from 
						consolidated_gaps cg
					where 
						si.serial_id = cg.serial_id
							and
						si.ser_idx = cg.ser_idx
							and
						si.platform_id = cg.platform_id
							and 
						tsrange(si.serial_participant_start,
								si.serial_participant_end,
								'[]'
								) @> cg.start_time
				)
),
act_with_same_part_and_gap_start as (
	select
		cg.start_time,
		cg.start_time end_time,
		cg.platform_id,
		cg.serial_id,
		cg.ser_idx
	from
		consolidated_gap_ranks cg
			inner join
		state_time_rankings s
				on cg.serial_id = s.serial_id
				and cg.ser_idx = s.ser_idx
				and cg.platform_id = s.platform_id
				and cg.rowno = 1
				and cg.start_time =  s.time
			inner join
		sensors_involved si
				on si.serial_participant_start = cg.start_time
				and si.platform_id = cg.platform_id
				and si.serial_id = cg.serial_id
				and si.ser_idx = cg.ser_idx
),
act_with_same_part_and_gap_end as (
	select
		cg.end_time start_time,
		cg.end_time,
		cg.platform_id,
		cg.serial_id,
		cg.ser_idx
	from
		consolidated_gap_ranks cg
			inner join
		state_time_rankings s
				on cg.serial_id = s.serial_id
				and cg.ser_idx = s.ser_idx
				and cg.platform_id = s.platform_id
				and cg.rowno = (select
									max(cgrs1.rowno)
								from
									consolidated_gap_ranks cgrs1
								where
									cgrs1.serial_id = cg.serial_id
										and
									cgrs1.ser_idx = cg.ser_idx
										and
									cgrs1.platform_id = cg.platform_id)
				and cg.end_time =  s.time
			inner join
		sensors_involved si
				on si.serial_participant_end = cg.end_time
				and si.platform_id = cg.platform_id
				and si.serial_id = cg.serial_id
				and si.ser_idx = cg.ser_idx
),
inner_coverage as (
	select
		cgrs.end_time start_time,
		cgre.start_time end_time,
		cgrs.platform_id,
		cgrs.serial_id,
		cgrs.ser_idx
	from
		consolidated_gap_ranks cgrs
			inner join
		consolidated_gap_ranks cgre
				on cgrs.platform_id = cgre.platform_id
				and cgrs.serial_id = cgre.serial_id
				and cgrs.ser_idx = cgre.ser_idx
				and cgrs.rowno=cgre.rowno-1
),
coverage_at_serial_start as (
	select
		pp.serial_participant_start start_time,
		cgrs.start_time end_time,
		cgrs.platform_id,
		cgrs.serial_id,
		cgrs.ser_idx
	from
		consolidated_gap_ranks cgrs
			inner join
		participating_platforms pp
				on cgrs.platform_id = pp.platform_id
				and cgrs.serial_id = pp.serial_id
				and cgrs.ser_idx = pp.ser_idx
				and cgrs.rowno = 1
				and cgrs.start_time != pp.serial_participant_start
),
coverage_at_serial_end as (
	select
		cgrs.end_time start_time,
		pp.serial_participant_end end_time,
		cgrs.platform_id,
		cgrs.serial_id,
		cgrs.ser_idx
	from
		consolidated_gap_ranks cgrs
			inner join
		participating_platforms pp
				on cgrs.platform_id = pp.platform_id
				and cgrs.serial_id = pp.serial_id
				and cgrs.ser_idx = pp.ser_idx
				and cgrs.rowno = (select
									max(cgrs1.rowno)
								from
									consolidated_gap_ranks cgrs1
								where
									cgrs1.serial_id = cgrs.serial_id
										and
									cgrs1.ser_idx = cgrs.ser_idx
										and
									cgrs1.platform_id = cgrs.platform_id)
				and pp.serial_participant_end != cgrs.end_time
),
consolidated_coverage as (
	select
		start_time,
		end_time,
		platform_id,
		serial_id,
		ser_idx
	from
		inner_coverage ic
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id,
		ser_idx
	from
		coverage_at_serial_start
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id,
		ser_idx
	from
		coverage_at_serial_end
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id,
		ser_idx
	from
		participation_sans_gap
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id,
		ser_idx
	from
		act_with_same_part_and_gap_start
	union all
	select
		start_time,
		end_time,
		platform_id,
		serial_id,
		ser_idx
	from
		act_with_same_part_and_gap_end
),
consolidated_coverage_with_created as (
	select
		case
			when
				strstart.created_date is null
			then
				strend.created_date
			when
				strend.created_date is null
			then
				strstart.created_date
			when
				strstart.created_date > strend.created_date
			then
				strstart.created_date
			else
				strend.created_date
		end created,
		cc.start_time,
		cc.end_time,
		cc.platform_id,
		cc.serial_id,
		cc.ser_idx
	from
		consolidated_coverage cc
			left join
		state_time_rankings strstart
				on (cc.platform_id, cc.serial_id, cc.ser_idx, cc.start_time)
					=(strstart.platform_id, strstart.serial_id, strstart.ser_idx, strstart.time)
			left join
		state_time_rankings strend
				on (cc.platform_id, cc.serial_id, cc.ser_idx, cc.end_time)
					=(strend.platform_id, strend.serial_id, strend.ser_idx, strend.time)
),
consolidated_stats as (
	select 
		'C' range_type,
		start_time,
		end_time,
		created,
		platform_id,
		serial_id,
		ser_idx
	from
		consolidated_coverage_with_created
	union all
	select 
		'G' range_type,
		start_time,
		end_time,
		null created,
		platform_id,
		serial_id,
		ser_idx
	from
		consolidated_gaps
)
select
	cs.range_type,
	cs.start_time,
	cs.end_time,
	cs.created,
	cs.platform_id,
	ser.serial_number::text
from
	consolidated_stats cs
	left join
	pepys."Serials" ser
		on cs.serial_id = ser.serial_id
where
	range_type in (select
					range_type
				from
					range_types)
order by
	cs.serial_id asc,
	cs.platform_id asc,
	cs.start_time asc,
	cs.end_time asc;
end;
$$
language plpgsql;

