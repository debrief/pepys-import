--DROPING EXISTING PEPYS.COMMENTS_FOR FUNCTION
DROP FUNCTION IF EXISTS PEPYS.COMMENTS_FOR;

--CREATING PEPYS.COMMENTS_FOR FUNCTION
CREATE FUNCTION PEPYS.COMMENTS_FOR(
    INP_START_TIME TEXT,
    INP_END_TIME TEXT,
    INP_COMMENT_SEARCH_STRING TEXT,
    INP_PLATFORM_SOURCE_MAP TEXT,
    INP_PAGE_NO INTEGER DEFAULT -1,
    INP_PAGE_SIZE INTEGER DEFAULT -1)
RETURNS TABLE (
	comment_id UUID,
	comment_time TIMESTAMP WITHOUT TIME ZONE,
	platform_name varchar(150),
	platformtype_name varchar(150),
	nationality_name varchar(150),
	content text,
	comment_type_name varchar(150),
	reference varchar(150))
AS
$$
--Name: Comments_For
--Version: v0.18
	with
	ui_filter_input as
		(select
				inp_start_time start_time, --Input should be same as for Phase 1
				inp_end_time end_time,  --Input should be same as for Phase 1
				inp_comment_search_string comment_search_string, --Input should be same as for Phase 1
				inp_platform_source_map::text source_map, --Input for platform and source map
				inp_page_no::integer page_no, --Pagination input. Page No For ex. if there are 1000 records paginated into pages of 100 records each, 1 here will return the first page or first 100 records
				inp_page_size::integer page_size --Pagination input - No. of records per page
		),
		processed_ui_filter_values as
		(select
				case when (trim(ui_input.start_time)='' OR ui_input.start_time is null) then '1000-01-01 00:00:00.000000'::timestamp else to_timestamp(ui_input.start_time, 'YYYY-MM-DD HH24:MI:SS.US') end as start_time,
				case when (trim(ui_input.end_time)='' OR ui_input.end_time is null) then '9999-12-12 23:59:59.000000'::timestamp else to_timestamp(ui_input.end_time, 'YYYY-MM-DD HH24:MI:SS.US') end as end_time,
				case when (trim(ui_input.comment_search_string)='' OR ui_input.comment_search_string is null) then null::varchar else '%'||upper(ui_input.comment_search_string)||'%' end as comment_search_string
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
		platform_source_maps as
		(
			select
				(psmap).key::uuid platform_id,
				json_array_elements_text((psmap).value)::uuid source_id
			from
				source_map_values
		),
		filtered_comments as
		(
			select
				com.comment_id,
				com.time,
				com.content,
				com.source_id,
				com.platform_id,
				com.comment_type_id
			from
				pepys."Comments" com
			where
				--Start and End Time criteria from the UI
				tsrange((select start_time::timestamp from processed_ui_filter_values), (select end_time::timestamp from processed_ui_filter_values), '[]') @> com.time AND
				--Comment search criteria from the UI
				((select comment_search_string from processed_ui_filter_values) is null OR upper(com.content) like (select comment_search_string from processed_ui_filter_values)) AND
				((select source_map from ui_filter_input) is null OR (com.source_id, com.platform_id) in (select source_id, platform_id from platform_source_maps))
		),
		filtered_limits as
		(select
			case when (ui_input.page_no = -1 OR ui_input.page_size = -1) then 1 else ui_input.page_no end as page_no,
			case when (ui_input.page_no = -1 OR ui_input.page_size = -1) then (select count(1) from filtered_comments) else ui_input.page_size end as page_size
		from
			ui_filter_input as ui_input
		)
	select filtered_comments.comment_id, filtered_comments.time, Platforms.name,
			PlatformTypes.name, Nationalities.name,
			filtered_comments.content, CommentTypes.name,
			Datafiles.reference from
			filtered_comments inner join
			pepys."Datafiles" as Datafiles on Datafiles.datafile_id=filtered_comments.source_id inner join
			pepys."Platforms" as Platforms on filtered_comments.platform_id=Platforms.platform_id inner join
			pepys."PlatformTypes" as PlatformTypes on Platforms.platform_type_id = PlatformTypes.platform_type_id inner join
			pepys."Nationalities" as Nationalities on Platforms.nationality_id = Nationalities.nationality_id inner join
			pepys."CommentTypes" as CommentTypes on filtered_comments.comment_type_id = CommentTypes.comment_type_id
	--Sort clause for pagination
	order by
		filtered_comments.comment_id asc
	limit (select page_size from filtered_limits)
	offset (select page_size*(page_no -1) from filtered_limits);
$$
LANGUAGE SQL;
