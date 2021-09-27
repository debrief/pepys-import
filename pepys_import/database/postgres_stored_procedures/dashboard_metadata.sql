--droping existing pepys.dashboard_metadata function
drop function if exists pepys.dashboard_metadata;

--creating pepys.dashboard_metadata function
create function pepys.dashboard_metadata(
	ui_inp_start_date text,
	ui_inp_end_date text)
returns table (
	record_type text,
	include_in_timeline text,
	serial_id uuid,
	platform_id uuid,
	"name" text,
	exercise text,
	platform_type_name text,
	"start" timestamp without time zone,
	"end" timestamp without time zone,
	gap_seconds int,
	interval_missing text,
	force_type_name text,
	force_type_color text)
as
$$
begin
	return query
with
latest_serials as (
	select 
		s.serial_id,
		s.serial_number::text serial_name,
		s.exercise::text,
		coalesce(s.include_in_timeline, false)::text include_in_timeline,
		s.start serial_start,
		s.end serial_end
	from
		pepys."Serials" s
	where 
		--Identify all serials happening during the ui_inp_start_date and ui_inp_end_date
		s.start::date <= to_date(ui_inp_end_date, 'YYYY-MM-DD')
			and
		s.end::date >= to_date(ui_inp_start_date, 'YYYY-MM-DD')
),
participating_platforms as (
	select
		ep.platform_id,
		coalesce(p.quadgraph, upper(substring(p.name,1,4)))::text platform_name,
		coalesce(pt.default_data_interval_secs, 30) gap_seconds,
		pt.name::text platform_type_name,
		ls.serial_start,
		ls.serial_end,
		coalesce(sp.start, ls.serial_start) serial_participant_start,
		coalesce(sp.end, ls.serial_end) serial_participant_end,
		sp.serial_id,
		case
			when
				pt.default_data_interval_secs is null
			then
				true
			when
				pt.default_data_interval_secs <= 0
			then
				true
			else
				false
		end::text interval_missing,
		ft.name::text force_type_name,
		ft.color::text force_type_color
	from
		pepys."SerialParticipants" sp
			inner join
		pepys."WargameParticipants" ep
				on sp.wargame_participant_id = ep.wargame_participant_id
			inner join
		pepys."Platforms" p
				on p.platform_id = ep.platform_id
			inner join
		pepys."PlatformTypes" pt
				on p.platform_type_id = pt.platform_type_id
			inner join
		pepys."ForceTypes" ft
				on ft.force_type_id=sp.force_type_id
			inner join
		latest_serials ls
				on ls.serial_id = sp.serial_id
)
select
	'SERIALS' record_type,
	s.include_in_timeline,
	s.serial_id,
	NULL platform_id,
	s.serial_name "name",
	s.exercise,
	NULL platform_type_name,
	s.serial_start "start",
	s.serial_end "end",
	NULL gap_seconds,
	NULL interval_missing,
	NULL::text force_type_name,
	NULL::text force_type_color
from
	latest_serials s
union all
select
	'SERIAL PARTICIPANT' record_type,
	NULL include_in_timeline,
	pp.serial_id,
	pp.platform_id,
	coalesce(pp.platform_name, 'PLT1') "name",
	NULL exercise,
	pp.platform_type_name,
	pp.serial_participant_start "start",
	pp.serial_participant_end "end",
	pp.gap_seconds,
	pp.interval_missing,
	pp.force_type_name,
	pp.force_type_color
from
	participating_platforms pp
order by 
	record_type desc,
	"name",
	"start",
	"end";
end;
$$
language plpgsql;

