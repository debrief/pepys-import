--
-- PostgreSQL database dump
--

-- Dumped from database version 11.3
-- Dumped by pg_dump version 11.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- Name: record_type; Type: TYPE; Schema: public; Owner: tracstor_admin
--

CREATE TYPE public.record_type AS (
    platform text,
    serial text,
    sensor text,
    heading numeric,
    course text,
    speed text,
    source text,
    privacy text,
    depth text,
    es_index text
    );


ALTER TYPE public.record_type OWNER TO tracstor_admin;

--
-- Name: cs_refresh_mviews(); Type: FUNCTION; Schema: public; Owner: tracstor_admin
--

CREATE FUNCTION public.cs_refresh_mviews() RETURNS void
    LANGUAGE plpgsql
AS
$$
DECLARE
    mviews RECORD;
BEGIN
    FOR mviews in
        (select *
         from jsonb_array_elements('[
           {
             "platform": "Frigate",
             "serial": "EX_ALPHA",
             "sensor": "GPS",
             "heading": 0,
             "course": "",
             "speed": "",
             "source": "CD_123",
             "privacy": "public",
             "depth": "",
             "es_index": "states"
           }
         ]'))
        LOOP
            Raise Notice '%', mviews ->> 'platform';
        END LOOP;
END;
$$;


ALTER FUNCTION public.cs_refresh_mviews() OWNER TO tracstor_admin;

--
-- Name: cs_refresh_mviews(jsonb); Type: FUNCTION; Schema: public; Owner: tracstor_admin
--

CREATE FUNCTION public.cs_refresh_mviews(input_text jsonb) RETURNS void
    LANGUAGE plpgsql
AS
$$
DECLARE
    mviews json;
BEGIN
    FOR mviews in
        (select * from jsonb_array_elements(input_text))
        LOOP
        --INSERT INTO PLATFORM OR GET EXISTING PLATFORM ID
        --INSERT INTO SENSOR OR GET EXISTING SENSOR ID
        --GET THE SOURCE ID FROM DATAFILES TABLE
            Raise '%s', mviews ->> 'platform';
        END LOOP;
END;
$$;


ALTER FUNCTION public.cs_refresh_mviews(input_text jsonb) OWNER TO tracstor_admin;

--
-- Name: insert_from_json(json); Type: FUNCTION; Schema: public; Owner: tracstor_admin
--

CREATE FUNCTION public.insert_from_json(in_json_txt json) RETURNS void
    LANGUAGE sql
AS
$$
Insert into "test"(platform, serialno)
SELECT (rec ->> 'platform')::text, (rec ->> 'serial')::text
FROM json_array_elements(in_json_txt -> 'data') rec
$$;


ALTER FUNCTION public.insert_from_json(in_json_txt json) OWNER TO tracstor_admin;

--
-- Name: log_state_changes(); Type: FUNCTION; Schema: public; Owner: tracstor_admin
--

CREATE FUNCTION public.log_state_changes() RETURNS trigger
    LANGUAGE plpgsql
AS
$$
BEGIN
    IF NEW.time <> OLD.time THEN
        INSERT INTO "ChangeLog"(tabletype_id, entry_id, "column", old_value,
                                new_value, changed_date)
        VALUES (1, old.state_id, "time", OLD.time, new.time, Now());
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.log_state_changes() OWNER TO tracstor_admin;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: Activations; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Activations"
(
    sensor_id     uuid DEFAULT public.gen_random_uuid() NOT NULL,
    "end"         timestamp without time zone           NOT NULL,
    min_range     double precision,
    max_range     double precision,
    left_arc      double precision,
    right_arc     double precision,
    datafile_id   uuid                                  NOT NULL,
    privacy_id    uuid,
    name          character varying(150)                NOT NULL,
    activation_id uuid                                  NOT NULL,
    start         timestamp without time zone           NOT NULL
);


ALTER TABLE public."Activations"
    OWNER TO tracstor_admin;

--
-- Name: ChangeLog; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."ChangeLog"
(
    changelog_id integer NOT NULL,
    tabletype_id integer,
    entry_id     uuid,
    "column"     character varying(100),
    old_value    character varying(250),
    new_value    character varying(250),
    changed_by   integer,
    changed_date timestamp without time zone
);


ALTER TABLE public."ChangeLog"
    OWNER TO tracstor_admin;

--
-- Name: Contacts; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Contacts"
(
    contact_id  uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name        character varying(150)                NOT NULL,
    sensor_id   uuid                                  NOT NULL,
    "time"      timestamp without time zone           NOT NULL,
    bearing     double precision,
    freq        double precision,
    location    point,
    major       double precision,
    minor       double precision,
    orientation double precision,
    datafile_id uuid                                  NOT NULL,
    privacy_id  uuid
);


ALTER TABLE public."Contacts"
    OWNER TO tracstor_admin;

--
-- Name: DatafileTypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."DatafileTypes"
(
    datafiletype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name            character varying(150)                NOT NULL
);


ALTER TABLE public."DatafileTypes"
    OWNER TO tracstor_admin;

--
-- Name: Datafiles; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Datafiles"
(
    datafile_id     uuid DEFAULT public.gen_random_uuid() NOT NULL,
    simulated       boolean,
    reference       character varying(150),
    url             character varying(500),
    privacy_id      uuid                                  NOT NULL,
    datafiletype_id uuid                                  NOT NULL
);


ALTER TABLE public."Datafiles"
    OWNER TO tracstor_admin;

--
-- Name: Entry; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Entry"
(
    entry_id     uuid DEFAULT public.gen_random_uuid() NOT NULL,
    tabletype_id integer                               NOT NULL,
    created_user integer
);


ALTER TABLE public."Entry"
    OWNER TO tracstor_admin;

--
-- Name: EntryTags; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."EntryTags"
(
    entry_id     uuid DEFAULT public.gen_random_uuid() NOT NULL,
    tag_id       integer                               NOT NULL,
    created_user integer,
    "IsPrivate"  boolean
);


ALTER TABLE public."EntryTags"
    OWNER TO tracstor_admin;

--
-- Name: EntryTypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."EntryTypes"
(
    entrytype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name         character varying(150)                NOT NULL
);


ALTER TABLE public."EntryTypes"
    OWNER TO tracstor_admin;

--
-- Name: Geometries; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Geometries"
(
    geometry_id         uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name                character varying(150)                NOT NULL,
    geometrytype_id     uuid                                  NOT NULL,
    geometrysubtype_id  uuid                                  NOT NULL,
    start               timestamp without time zone,
    "end"               timestamp without time zone,
    task_id             uuid,
    subject_platform_id uuid,
    sensor_platform_id  uuid,
    datafile_id         uuid                                  NOT NULL,
    privacy_id          uuid
);


ALTER TABLE public."Geometries"
    OWNER TO tracstor_admin;

--
-- Name: GeometrySubTypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."GeometrySubTypes"
(
    geometrysubtype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name               character varying(150)                NOT NULL,
    geometrytype_id    uuid                                  NOT NULL
);


ALTER TABLE public."GeometrySubTypes"
    OWNER TO tracstor_admin;

--
-- Name: GeometryTypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."GeometryTypes"
(
    geometrytype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name            character varying(150)                NOT NULL
);


ALTER TABLE public."GeometryTypes"
    OWNER TO tracstor_admin;

--
-- Name: Media; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Media"
(
    media_id            uuid DEFAULT public.gen_random_uuid() NOT NULL,
    source_platform_id  uuid,
    subject_platform_id uuid,
    sensor_id           uuid,
    location            point,
    "time"              timestamp without time zone,
    mediatype_id        uuid                                  NOT NULL,
    url                 character varying(500)                NOT NULL,
    datafile_id         uuid                                  NOT NULL,
    privacy_id          uuid
);


ALTER TABLE public."Media"
    OWNER TO tracstor_admin;

--
-- Name: MediaTypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."MediaTypes"
(
    mediatype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name         character varying(150)                NOT NULL
);


ALTER TABLE public."MediaTypes"
    OWNER TO tracstor_admin;

--
-- Name: NarrativeEntries; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."NarrativeEntries"
(
    narrativeentry_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    platform_id       uuid,
    "time"            timestamp without time zone           NOT NULL,
    entrytype_id      uuid                                  NOT NULL,
    content           text                                  NOT NULL,
    datafile_id       uuid                                  NOT NULL,
    privacy_id        uuid
);


ALTER TABLE public."NarrativeEntries"
    OWNER TO tracstor_admin;

--
-- Name: Nationalities; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Nationalities"
(
    nationality_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name           character varying(150)                NOT NULL
);


ALTER TABLE public."Nationalities"
    OWNER TO tracstor_admin;

--
-- Name: Participation; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Participation"
(
    participation_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    platform_id      uuid                                  NOT NULL,
    task_id          uuid                                  NOT NULL,
    start            time without time zone,
    "end"            time without time zone,
    force            character varying(150)
);


ALTER TABLE public."Participation"
    OWNER TO tracstor_admin;

--
-- Name: PlatformTypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."PlatformTypes"
(
    platformtype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name            character varying(150)                NOT NULL
);


ALTER TABLE public."PlatformTypes"
    OWNER TO tracstor_admin;

--
-- Name: Platforms; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Platforms"
(
    platform_id      uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name             character varying(150)                NOT NULL,
    platformtype_id  uuid                                  NOT NULL,
    host_platform_id uuid,
    nationality_id   uuid                                  NOT NULL
);


ALTER TABLE public."Platforms"
    OWNER TO tracstor_admin;

--
-- Name: Privacies; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Privacies"
(
    privacy_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name       character varying(150)                NOT NULL
);


ALTER TABLE public."Privacies"
    OWNER TO tracstor_admin;

--
-- Name: SensorTypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."SensorTypes"
(
    sensortype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name          character varying(150)                NOT NULL
);


ALTER TABLE public."SensorTypes"
    OWNER TO tracstor_admin;

--
-- Name: Sensors; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Sensors"
(
    sensor_id     uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name          character varying(150)                NOT NULL,
    sensortype_id uuid                                  NOT NULL,
    platform_id   uuid                                  NOT NULL
);


ALTER TABLE public."Sensors"
    OWNER TO tracstor_admin;

--
-- Name: State; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."State"
(
    state_id    uuid DEFAULT public.gen_random_uuid() NOT NULL,
    "time"      timestamp without time zone           NOT NULL,
    sensor_id   uuid                                  NOT NULL,
    location    point,
    heading     double precision,
    course      double precision,
    speed       double precision,
    datafile_id uuid                                  NOT NULL,
    privacy_id  uuid
);


ALTER TABLE public."State"
    OWNER TO tracstor_admin;

--
-- Name: TableTypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."TableTypes"
(
    tabletype_id integer                NOT NULL,
    name         character varying(150) NOT NULL
);


ALTER TABLE public."TableTypes"
    OWNER TO tracstor_admin;

--
-- Name: Tags; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Tags"
(
    tag_id       integer                NOT NULL,
    tag_text     character varying(500) NOT NULL,
    created_user integer                NOT NULL
);


ALTER TABLE public."Tags"
    OWNER TO tracstor_admin;

--
-- Name: Tasks; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Tasks"
(
    task_id       uuid DEFAULT public.gen_random_uuid() NOT NULL,
    parenttask_id uuid,
    start         timestamp without time zone           NOT NULL,
    "end"         timestamp without time zone           NOT NULL,
    environment   character varying(150),
    location      point
);


ALTER TABLE public."Tasks"
    OWNER TO tracstor_admin;

--
-- Name: Users; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public."Users"
(
    user_id   integer                NOT NULL,
    user_name character varying(150) NOT NULL
);


ALTER TABLE public."Users"
    OWNER TO tracstor_admin;

--
-- Name: Users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: tracstor_admin
--

CREATE SEQUENCE public."Users_user_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Users_user_id_seq"
    OWNER TO tracstor_admin;

--
-- Name: Users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tracstor_admin
--

ALTER SEQUENCE public."Users_user_id_seq" OWNED BY public."Users".user_id;


--
-- Name: test; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.test
(
    platform character varying,
    serialno character varying
);


ALTER TABLE public.test
    OWNER TO tracstor_admin;

--
-- Name: Users user_id; Type: DEFAULT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Users"
    ALTER COLUMN user_id SET DEFAULT nextval(
            'public."Users_user_id_seq"'::regclass);


--
-- Name: Activations Activations_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Activations"
    ADD CONSTRAINT "Activations_pkey" PRIMARY KEY (activation_id);


--
-- Name: ChangeLog ChangeLog_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."ChangeLog"
    ADD CONSTRAINT "ChangeLog_pkey" PRIMARY KEY (changelog_id);


--
-- Name: Contacts Contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Contacts"
    ADD CONSTRAINT "Contacts_pkey" PRIMARY KEY (contact_id);


--
-- Name: DatafileTypes DatafileTypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."DatafileTypes"
    ADD CONSTRAINT "DatafileTypes_pkey" PRIMARY KEY (datafiletype_id);


--
-- Name: Datafiles Datafiles_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Datafiles"
    ADD CONSTRAINT "Datafiles_pkey" PRIMARY KEY (datafile_id);


--
-- Name: EntryTypes EntryTypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."EntryTypes"
    ADD CONSTRAINT "EntryTypes_pkey" PRIMARY KEY (entrytype_id);


--
-- Name: Entry Entry_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Entry"
    ADD CONSTRAINT "Entry_pkey" PRIMARY KEY (entry_id);


--
-- Name: Geometries Geometries_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Geometries"
    ADD CONSTRAINT "Geometries_pkey" PRIMARY KEY (geometry_id);


--
-- Name: GeometrySubTypes GeometrySubTypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."GeometrySubTypes"
    ADD CONSTRAINT "GeometrySubTypes_pkey" PRIMARY KEY (geometrysubtype_id);


--
-- Name: GeometryTypes GeometryTypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."GeometryTypes"
    ADD CONSTRAINT "GeometryTypes_pkey" PRIMARY KEY (geometrytype_id);


--
-- Name: MediaTypes MediaTypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."MediaTypes"
    ADD CONSTRAINT "MediaTypes_pkey" PRIMARY KEY (mediatype_id);


--
-- Name: Media Media_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Media"
    ADD CONSTRAINT "Media_pkey" PRIMARY KEY (media_id);


--
-- Name: NarrativeEntries NarrativeEntries_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."NarrativeEntries"
    ADD CONSTRAINT "NarrativeEntries_pkey" PRIMARY KEY (narrativeentry_id);


--
-- Name: Nationalities Nationalities_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Nationalities"
    ADD CONSTRAINT "Nationalities_pkey" PRIMARY KEY (nationality_id);


--
-- Name: Participation Participation_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Participation"
    ADD CONSTRAINT "Participation_pkey" PRIMARY KEY (participation_id);


--
-- Name: PlatformTypes PlatformTypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."PlatformTypes"
    ADD CONSTRAINT "PlatformTypes_pkey" PRIMARY KEY (platformtype_id);


--
-- Name: Platforms Platforms_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Platforms"
    ADD CONSTRAINT "Platforms_pkey" PRIMARY KEY (platform_id);


--
-- Name: Privacies Privacies_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Privacies"
    ADD CONSTRAINT "Privacies_pkey" PRIMARY KEY (privacy_id);


--
-- Name: SensorTypes SensorTypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."SensorTypes"
    ADD CONSTRAINT "SensorTypes_pkey" PRIMARY KEY (sensortype_id);


--
-- Name: Sensors Sensors_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Sensors"
    ADD CONSTRAINT "Sensors_pkey" PRIMARY KEY (sensor_id);


--
-- Name: State State_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."State"
    ADD CONSTRAINT "State_pkey" PRIMARY KEY (state_id);


--
-- Name: TableTypes TableTypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."TableTypes"
    ADD CONSTRAINT "TableTypes_pkey" PRIMARY KEY (tabletype_id);


--
-- Name: Tags Tags_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Tags"
    ADD CONSTRAINT "Tags_pkey" PRIMARY KEY (tag_id);


--
-- Name: Tasks Tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Tasks"
    ADD CONSTRAINT "Tasks_pkey" PRIMARY KEY (task_id);


--
-- Name: Users Users_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Users"
    ADD CONSTRAINT "Users_pkey" PRIMARY KEY (user_id);


--
-- Name: Activations activations_datafiles_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Activations"
    ADD CONSTRAINT activations_datafiles_fk FOREIGN KEY (datafile_id) REFERENCES public."Datafiles" (datafile_id);


--
-- Name: Activations activations_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Activations"
    ADD CONSTRAINT activations_entry_fk FOREIGN KEY (activation_id) REFERENCES public."Entry" (entry_id);


--
-- Name: Activations activations_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Activations"
    ADD CONSTRAINT activations_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public."Privacies" (privacy_id);


--
-- Name: Activations activations_sensors_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Activations"
    ADD CONSTRAINT activations_sensors_fk FOREIGN KEY (sensor_id) REFERENCES public."Sensors" (sensor_id);


--
-- Name: Contacts contacts_datafiles_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Contacts"
    ADD CONSTRAINT contacts_datafiles_fk FOREIGN KEY (datafile_id) REFERENCES public."Datafiles" (datafile_id);


--
-- Name: Contacts contacts_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Contacts"
    ADD CONSTRAINT contacts_entry_fk FOREIGN KEY (contact_id) REFERENCES public."Entry" (entry_id);


--
-- Name: Contacts contacts_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Contacts"
    ADD CONSTRAINT contacts_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public."Privacies" (privacy_id);


--
-- Name: Contacts contacts_sensors_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Contacts"
    ADD CONSTRAINT contacts_sensors_fk FOREIGN KEY (sensor_id) REFERENCES public."Sensors" (sensor_id);


--
-- Name: Datafiles datafiles_datafiletypes_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Datafiles"
    ADD CONSTRAINT datafiles_datafiletypes_fk FOREIGN KEY (datafiletype_id) REFERENCES public."DatafileTypes" (datafiletype_id);


--
-- Name: Datafiles datafiles_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Datafiles"
    ADD CONSTRAINT datafiles_entry_fk FOREIGN KEY (datafile_id) REFERENCES public."Entry" (entry_id);


--
-- Name: Datafiles datafiles_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Datafiles"
    ADD CONSTRAINT datafiles_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public."Privacies" (privacy_id);


--
-- Name: Entry entry_tabletypes_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Entry"
    ADD CONSTRAINT entry_tabletypes_fk FOREIGN KEY (tabletype_id) REFERENCES public."TableTypes" (tabletype_id);


--
-- Name: Entry entry_users_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Entry"
    ADD CONSTRAINT entry_users_fk FOREIGN KEY (created_user) REFERENCES public."Users" (user_id);


--
-- Name: EntryTags entrytags_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."EntryTags"
    ADD CONSTRAINT entrytags_entry_fk FOREIGN KEY (entry_id) REFERENCES public."Entry" (entry_id);


--
-- Name: EntryTags entrytags_tags_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."EntryTags"
    ADD CONSTRAINT entrytags_tags_fk FOREIGN KEY (tag_id) REFERENCES public."Tags" (tag_id);


--
-- Name: EntryTags entrytags_users_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."EntryTags"
    ADD CONSTRAINT entrytags_users_fk FOREIGN KEY (created_user) REFERENCES public."Users" (user_id);


--
-- Name: Geometries geometries_datafiles_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Geometries"
    ADD CONSTRAINT geometries_datafiles_fk FOREIGN KEY (datafile_id) REFERENCES public."Datafiles" (datafile_id);


--
-- Name: Geometries geometries_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Geometries"
    ADD CONSTRAINT geometries_entry_fk FOREIGN KEY (geometry_id) REFERENCES public."Entry" (entry_id);


--
-- Name: Geometries geometries_geometrysubtype_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Geometries"
    ADD CONSTRAINT geometries_geometrysubtype_fk FOREIGN KEY (geometrysubtype_id) REFERENCES public."GeometrySubTypes" (geometrysubtype_id);


--
-- Name: Geometries geometries_geometrytype_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Geometries"
    ADD CONSTRAINT geometries_geometrytype_fk FOREIGN KEY (geometrytype_id) REFERENCES public."GeometryTypes" (geometrytype_id);


--
-- Name: Geometries geometries_platform_sensors_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Geometries"
    ADD CONSTRAINT geometries_platform_sensors_fk FOREIGN KEY (sensor_platform_id) REFERENCES public."Platforms" (platform_id);


--
-- Name: Geometries geometries_platform_subject_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Geometries"
    ADD CONSTRAINT geometries_platform_subject_fk FOREIGN KEY (subject_platform_id) REFERENCES public."Platforms" (platform_id);


--
-- Name: Geometries geometries_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Geometries"
    ADD CONSTRAINT geometries_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public."Privacies" (privacy_id);


--
-- Name: Geometries geometries_task_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Geometries"
    ADD CONSTRAINT geometries_task_fk FOREIGN KEY (task_id) REFERENCES public."Tasks" (task_id);


--
-- Name: GeometrySubTypes geometrysubtypes_geometrytype_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."GeometrySubTypes"
    ADD CONSTRAINT geometrysubtypes_geometrytype_fk FOREIGN KEY (geometrytype_id) REFERENCES public."GeometryTypes" (geometrytype_id);


--
-- Name: Media media_datafiles_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Media"
    ADD CONSTRAINT media_datafiles_fk FOREIGN KEY (datafile_id) REFERENCES public."Datafiles" (datafile_id);


--
-- Name: Media media_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Media"
    ADD CONSTRAINT media_entry_fk FOREIGN KEY (media_id) REFERENCES public."Entry" (entry_id);


--
-- Name: Media media_mediatype_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Media"
    ADD CONSTRAINT media_mediatype_fk FOREIGN KEY (mediatype_id) REFERENCES public."MediaTypes" (mediatype_id);


--
-- Name: Media media_platform_source_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Media"
    ADD CONSTRAINT media_platform_source_fk FOREIGN KEY (source_platform_id) REFERENCES public."Platforms" (platform_id);


--
-- Name: Media media_platform_subject_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Media"
    ADD CONSTRAINT media_platform_subject_fk FOREIGN KEY (subject_platform_id) REFERENCES public."Platforms" (platform_id);


--
-- Name: Media media_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Media"
    ADD CONSTRAINT media_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public."Privacies" (privacy_id);


--
-- Name: Media media_sensor_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Media"
    ADD CONSTRAINT media_sensor_fk FOREIGN KEY (sensor_id) REFERENCES public."Sensors" (sensor_id);


--
-- Name: NarrativeEntries narrativeentries_datafiles_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."NarrativeEntries"
    ADD CONSTRAINT narrativeentries_datafiles_fk FOREIGN KEY (datafile_id) REFERENCES public."Datafiles" (datafile_id);


--
-- Name: NarrativeEntries narrativeentries_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."NarrativeEntries"
    ADD CONSTRAINT narrativeentries_entry_fk FOREIGN KEY (narrativeentry_id) REFERENCES public."Entry" (entry_id);


--
-- Name: NarrativeEntries narrativeentries_entrytypes_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."NarrativeEntries"
    ADD CONSTRAINT narrativeentries_entrytypes_fk FOREIGN KEY (entrytype_id) REFERENCES public."EntryTypes" (entrytype_id);


--
-- Name: NarrativeEntries narrativeentries_platform_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."NarrativeEntries"
    ADD CONSTRAINT narrativeentries_platform_fk FOREIGN KEY (platform_id) REFERENCES public."Platforms" (platform_id);


--
-- Name: NarrativeEntries narrativeentries_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."NarrativeEntries"
    ADD CONSTRAINT narrativeentries_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public."Privacies" (privacy_id);


--
-- Name: Participation participation_platform_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Participation"
    ADD CONSTRAINT participation_platform_fk FOREIGN KEY (platform_id) REFERENCES public."Platforms" (platform_id);


--
-- Name: Participation participation_tasks_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Participation"
    ADD CONSTRAINT participation_tasks_fk FOREIGN KEY (task_id) REFERENCES public."Tasks" (task_id);


--
-- Name: Platforms platforms_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Platforms"
    ADD CONSTRAINT platforms_entry_fk FOREIGN KEY (platform_id) REFERENCES public."Entry" (entry_id);


--
-- Name: Platforms platforms_nationalities_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Platforms"
    ADD CONSTRAINT platforms_nationalities_fk FOREIGN KEY (nationality_id) REFERENCES public."Nationalities" (nationality_id);


--
-- Name: Platforms platforms_platforms_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Platforms"
    ADD CONSTRAINT platforms_platforms_fk FOREIGN KEY (host_platform_id) REFERENCES public."Platforms" (platform_id);


--
-- Name: Platforms platforms_platformtypes_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Platforms"
    ADD CONSTRAINT platforms_platformtypes_fk FOREIGN KEY (platformtype_id) REFERENCES public."PlatformTypes" (platformtype_id);


--
-- Name: Sensors sensor_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Sensors"
    ADD CONSTRAINT sensor_entry_fk FOREIGN KEY (sensor_id) REFERENCES public."Entry" (entry_id);


--
-- Name: Sensors sensor_platforms_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Sensors"
    ADD CONSTRAINT sensor_platforms_fk FOREIGN KEY (platform_id) REFERENCES public."Platforms" (platform_id);


--
-- Name: Sensors sensor_sensortypes_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Sensors"
    ADD CONSTRAINT sensor_sensortypes_fk FOREIGN KEY (sensortype_id) REFERENCES public."SensorTypes" (sensortype_id);


--
-- Name: State state_datafiles_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."State"
    ADD CONSTRAINT state_datafiles_fk FOREIGN KEY (datafile_id) REFERENCES public."Datafiles" (datafile_id);


--
-- Name: State state_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."State"
    ADD CONSTRAINT state_entry_fk FOREIGN KEY (state_id) REFERENCES public."Entry" (entry_id);


--
-- Name: State state_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."State"
    ADD CONSTRAINT state_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public."Privacies" (privacy_id);


--
-- Name: State state_sensors_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."State"
    ADD CONSTRAINT state_sensors_fk FOREIGN KEY (sensor_id) REFERENCES public."Sensors" (sensor_id);


--
-- Name: Tags tags_users_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Tags"
    ADD CONSTRAINT tags_users_fk FOREIGN KEY (created_user) REFERENCES public."Users" (user_id);


--
-- Name: Tasks tasks_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Tasks"
    ADD CONSTRAINT tasks_entry_fk FOREIGN KEY (task_id) REFERENCES public."Entry" (entry_id);


--
-- Name: Tasks tasks_tasks_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public."Tasks"
    ADD CONSTRAINT tasks_tasks_fk FOREIGN KEY (parenttask_id) REFERENCES public."Tasks" (task_id);


--
-- Name: FUNCTION cs_refresh_mviews(); Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON FUNCTION public.cs_refresh_mviews() TO tracstor_dev;


--
-- Name: FUNCTION cs_refresh_mviews(input_text jsonb); Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON FUNCTION public.cs_refresh_mviews(input_text jsonb) TO tracstor_dev;


--
-- Name: FUNCTION insert_from_json(in_json_txt json); Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON FUNCTION public.insert_from_json(in_json_txt json) TO tracstor_dev;


--
-- Name: FUNCTION log_state_changes(); Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON FUNCTION public.log_state_changes() TO tracstor_dev;


--
-- Name: TABLE "Activations"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Activations" TO tracstor_dev;


--
-- Name: TABLE "ChangeLog"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."ChangeLog" TO tracstor_dev;


--
-- Name: TABLE "Contacts"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Contacts" TO tracstor_dev;


--
-- Name: TABLE "DatafileTypes"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."DatafileTypes" TO tracstor_dev;


--
-- Name: TABLE "Datafiles"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Datafiles" TO tracstor_dev;


--
-- Name: TABLE "Entry"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Entry" TO tracstor_dev;


--
-- Name: TABLE "EntryTags"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."EntryTags" TO tracstor_dev;


--
-- Name: TABLE "EntryTypes"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."EntryTypes" TO tracstor_dev;


--
-- Name: TABLE "Geometries"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Geometries" TO tracstor_dev;


--
-- Name: TABLE "GeometrySubTypes"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."GeometrySubTypes" TO tracstor_dev;


--
-- Name: TABLE "GeometryTypes"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."GeometryTypes" TO tracstor_dev;


--
-- Name: TABLE "Media"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Media" TO tracstor_dev;


--
-- Name: TABLE "MediaTypes"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."MediaTypes" TO tracstor_dev;


--
-- Name: TABLE "NarrativeEntries"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."NarrativeEntries" TO tracstor_dev;


--
-- Name: TABLE "Nationalities"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Nationalities" TO tracstor_dev;


--
-- Name: TABLE "Participation"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Participation" TO tracstor_dev;


--
-- Name: TABLE "PlatformTypes"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."PlatformTypes" TO tracstor_dev;


--
-- Name: TABLE "Platforms"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Platforms" TO tracstor_dev;


--
-- Name: TABLE "Privacies"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Privacies" TO tracstor_dev;


--
-- Name: TABLE "SensorTypes"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."SensorTypes" TO tracstor_dev;


--
-- Name: TABLE "Sensors"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Sensors" TO tracstor_dev;


--
-- Name: TABLE "State"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."State" TO tracstor_dev;


--
-- Name: TABLE "TableTypes"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."TableTypes" TO tracstor_dev;


--
-- Name: TABLE "Tags"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Tags" TO tracstor_dev;


--
-- Name: TABLE "Tasks"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Tasks" TO tracstor_dev;


--
-- Name: TABLE "Users"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public."Users" TO tracstor_dev;


--
-- Name: SEQUENCE "Users_user_id_seq"; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON SEQUENCE public."Users_user_id_seq" TO tracstor_dev;


--
-- Name: TABLE test; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.test TO tracstor_dev;


--
-- PostgreSQL database dump complete
--

