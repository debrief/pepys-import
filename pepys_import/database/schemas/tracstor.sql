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

--CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'standard public schema';

--GRANT USAGE ON SCHEMA public TO postgres;
--CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


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
        INSERT INTO changelog(tabletype_id, entry_id, "column", old_value,
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
-- Name: activations; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.activations
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


ALTER TABLE public.activations
    OWNER TO tracstor_admin;

--
-- Name: changelog; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.changelog
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


ALTER TABLE public.changelog
    OWNER TO tracstor_admin;

--
-- Name: contacts; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.contacts
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


ALTER TABLE public.contacts
    OWNER TO tracstor_admin;

--
-- Name: datafiletypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.datafiletypes
(
    datafiletype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name            character varying(150)                NOT NULL
);


ALTER TABLE public.datafiletypes
    OWNER TO tracstor_admin;

--
-- Name: datafiles; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.datafiles
(
    datafile_id     uuid DEFAULT public.gen_random_uuid() NOT NULL,
    simulated       boolean,
    reference       character varying(150),
    url             character varying(500),
    privacy_id      uuid                                  NOT NULL,
    datafiletype_id uuid                                  NOT NULL
);


ALTER TABLE public.datafiles
    OWNER TO tracstor_admin;

--
-- Name: entry; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.entry
(
    entry_id     uuid DEFAULT public.gen_random_uuid() NOT NULL,
    tabletype_id integer                               NOT NULL,
    created_user integer
);


ALTER TABLE public.entry
    OWNER TO tracstor_admin;

--
-- Name: entrytags; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.entrytags
(
    entry_id     uuid DEFAULT public.gen_random_uuid() NOT NULL,
    tag_id       integer                               NOT NULL,
    created_user integer,
    "IsPrivate"  boolean
);


ALTER TABLE public.entrytags
    OWNER TO tracstor_admin;

--
-- Name: entrytypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.entrytypes
(
    entrytype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name         character varying(150)                NOT NULL
);


ALTER TABLE public.entrytypes
    OWNER TO tracstor_admin;

--
-- Name: geometries; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.geometries
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


ALTER TABLE public.geometries
    OWNER TO tracstor_admin;

--
-- Name: geometrysubtypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.geometrysubtypes
(
    geometrysubtype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name               character varying(150)                NOT NULL,
    geometrytype_id    uuid                                  NOT NULL
);


ALTER TABLE public.geometrysubtypes
    OWNER TO tracstor_admin;

--
-- Name: geometrytypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.geometrytypes
(
    geometrytype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name            character varying(150)                NOT NULL
);


ALTER TABLE public.geometrytypes
    OWNER TO tracstor_admin;

--
-- Name: media; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.media
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


ALTER TABLE public.media
    OWNER TO tracstor_admin;

--
-- Name: mediatypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.mediatypes
(
    mediatype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name         character varying(150)                NOT NULL
);


ALTER TABLE public.mediatypes
    OWNER TO tracstor_admin;

--
-- Name: narrativeentries; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.narrativeentries
(
    narrativeentry_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    platform_id       uuid,
    "time"            timestamp without time zone           NOT NULL,
    entrytype_id      uuid                                  NOT NULL,
    content           text                                  NOT NULL,
    datafile_id       uuid                                  NOT NULL,
    privacy_id        uuid
);


ALTER TABLE public.narrativeentries
    OWNER TO tracstor_admin;

--
-- Name: nationalities; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.nationalities
(
    nationality_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name           character varying(150)                NOT NULL
);


ALTER TABLE public.nationalities
    OWNER TO tracstor_admin;

--
-- Name: participation; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.participation
(
    participation_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    platform_id      uuid                                  NOT NULL,
    task_id          uuid                                  NOT NULL,
    start            time without time zone,
    "end"            time without time zone,
    force            character varying(150)
);


ALTER TABLE public.participation
    OWNER TO tracstor_admin;

--
-- Name: platformtypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.platformtypes
(
    platformtype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name            character varying(150)                NOT NULL
);


ALTER TABLE public.platformtypes
    OWNER TO tracstor_admin;

--
-- Name: platforms; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.platforms
(
    platform_id      uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name             character varying(150)                NOT NULL,
    platformtype_id  uuid                                  NOT NULL,
    host_platform_id uuid,
    nationality_id   uuid                                  NOT NULL
);


ALTER TABLE public.platforms
    OWNER TO tracstor_admin;

--
-- Name: privacies; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.privacies
(
    privacy_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name       character varying(150)                NOT NULL
);


ALTER TABLE public.privacies
    OWNER TO tracstor_admin;

--
-- Name: sensortypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.sensortypes
(
    sensortype_id uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name          character varying(150)                NOT NULL
);


ALTER TABLE public.sensortypes
    OWNER TO tracstor_admin;

--
-- Name: sensors; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.sensors
(
    sensor_id     uuid DEFAULT public.gen_random_uuid() NOT NULL,
    name          character varying(150)                NOT NULL,
    sensortype_id uuid                                  NOT NULL,
    platform_id   uuid                                  NOT NULL
);


ALTER TABLE public.sensors
    OWNER TO tracstor_admin;

--
-- Name: state; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.state
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


ALTER TABLE public.state
    OWNER TO tracstor_admin;

--
-- Name: tabletypes; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.tabletypes
(
    tabletype_id integer                NOT NULL,
    name         character varying(150) NOT NULL
);


ALTER TABLE public.tabletypes
    OWNER TO tracstor_admin;

--
-- Name: tags; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.tags
(
    tag_id       integer                NOT NULL,
    tag_text     character varying(500) NOT NULL,
    created_user integer                NOT NULL
);


ALTER TABLE public.tags
    OWNER TO tracstor_admin;

--
-- Name: tasks; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.tasks
(
    task_id       uuid DEFAULT public.gen_random_uuid() NOT NULL,
    parenttask_id uuid,
    start         timestamp without time zone           NOT NULL,
    "end"         timestamp without time zone           NOT NULL,
    environment   character varying(150),
    location      point
);


ALTER TABLE public.tasks
    OWNER TO tracstor_admin;

--
-- Name: users; Type: TABLE; Schema: public; Owner: tracstor_admin
--

CREATE TABLE public.users
(
    user_id   integer                NOT NULL,
    user_name character varying(150) NOT NULL
);


ALTER TABLE public.users
    OWNER TO tracstor_admin;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: tracstor_admin
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_user_id_seq
    OWNER TO tracstor_admin;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: tracstor_admin
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


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
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.users
    ALTER COLUMN user_id SET DEFAULT nextval(
            'public.users_user_id_seq'::regclass);


--
-- Name: activations activations_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.activations
    ADD CONSTRAINT activations_pkey PRIMARY KEY (activation_id);


--
-- Name: changelog changelog_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.changelog
    ADD CONSTRAINT changelog_pkey PRIMARY KEY (changelog_id);


--
-- Name: contacts contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_pkey PRIMARY KEY (contact_id);


--
-- Name: datafiletypes datafiletypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.datafiletypes
    ADD CONSTRAINT datafiletypes_pkey PRIMARY KEY (datafiletype_id);


--
-- Name: datafiles datafiles_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.datafiles
    ADD CONSTRAINT datafiles_pkey PRIMARY KEY (datafile_id);


--
-- Name: entrytypes entrytypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.entrytypes
    ADD CONSTRAINT entrytypes_pkey PRIMARY KEY (entrytype_id);


--
-- Name: entry entry_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.entry
    ADD CONSTRAINT entry_pkey PRIMARY KEY (entry_id);


--
-- Name: geometries geometries_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.geometries
    ADD CONSTRAINT geometries_pkey PRIMARY KEY (geometry_id);


--
-- Name: geometrysubtypes geometrysubtypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.geometrysubtypes
    ADD CONSTRAINT geometrysubtypes_pkey PRIMARY KEY (geometrysubtype_id);


--
-- Name: geometrytypes geometrytypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.geometrytypes
    ADD CONSTRAINT geometrytypes_pkey PRIMARY KEY (geometrytype_id);


--
-- Name: mediatypes mediatypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.mediatypes
    ADD CONSTRAINT mediatypes_pkey PRIMARY KEY (mediatype_id);


--
-- Name: media media_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.media
    ADD CONSTRAINT media_pkey PRIMARY KEY (media_id);


--
-- Name: narrativeentries narrativeentries_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.narrativeentries
    ADD CONSTRAINT narrativeentries_pkey PRIMARY KEY (narrativeentry_id);


--
-- Name: nationalities nationalities_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.nationalities
    ADD CONSTRAINT nationalities_pkey PRIMARY KEY (nationality_id);


--
-- Name: participation participation_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.participation
    ADD CONSTRAINT participation_pkey PRIMARY KEY (participation_id);


--
-- Name: platformtypes platformtypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.platformtypes
    ADD CONSTRAINT platformtypes_pkey PRIMARY KEY (platformtype_id);


--
-- Name: platforms platforms_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.platforms
    ADD CONSTRAINT platforms_pkey PRIMARY KEY (platform_id);


--
-- Name: privacies privacies_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.privacies
    ADD CONSTRAINT privacies_pkey PRIMARY KEY (privacy_id);


--
-- Name: sensortypes sensortypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.sensortypes
    ADD CONSTRAINT sensortypes_pkey PRIMARY KEY (sensortype_id);


--
-- Name: sensors sensors_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT sensors_pkey PRIMARY KEY (sensor_id);


--
-- Name: state state_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.state
    ADD CONSTRAINT state_pkey PRIMARY KEY (state_id);


--
-- Name: tabletypes tabletypes_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.tabletypes
    ADD CONSTRAINT tabletypes_pkey PRIMARY KEY (tabletype_id);


--
-- Name: tags tags_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (tag_id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (task_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: activations activations_datafiles_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.activations
    ADD CONSTRAINT activations_datafiles_fk FOREIGN KEY (datafile_id) REFERENCES public.datafiles (datafile_id);


--
-- Name: activations activations_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.activations
    ADD CONSTRAINT activations_entry_fk FOREIGN KEY (activation_id) REFERENCES public.entry (entry_id);


--
-- Name: activations activations_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.activations
    ADD CONSTRAINT activations_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public.privacies (privacy_id);


--
-- Name: activations activations_sensors_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.activations
    ADD CONSTRAINT activations_sensors_fk FOREIGN KEY (sensor_id) REFERENCES public.sensors (sensor_id);


--
-- Name: contacts contacts_datafiles_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_datafiles_fk FOREIGN KEY (datafile_id) REFERENCES public.datafiles (datafile_id);


--
-- Name: contacts contacts_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_entry_fk FOREIGN KEY (contact_id) REFERENCES public.entry (entry_id);


--
-- Name: contacts contacts_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public.privacies (privacy_id);


--
-- Name: contacts contacts_sensors_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_sensors_fk FOREIGN KEY (sensor_id) REFERENCES public.sensors (sensor_id);


--
-- Name: datafiles datafiles_datafiletypes_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.datafiles
    ADD CONSTRAINT datafiles_datafiletypes_fk FOREIGN KEY (datafiletype_id) REFERENCES public.datafiletypes (datafiletype_id);


--
-- Name: datafiles datafiles_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.datafiles
    ADD CONSTRAINT datafiles_entry_fk FOREIGN KEY (datafile_id) REFERENCES public.entry (entry_id);


--
-- Name: datafiles datafiles_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.datafiles
    ADD CONSTRAINT datafiles_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public.privacies (privacy_id);


--
-- Name: entry entry_tabletypes_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.entry
    ADD CONSTRAINT entry_tabletypes_fk FOREIGN KEY (tabletype_id) REFERENCES public.tabletypes (tabletype_id);


--
-- Name: entry entry_users_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.entry
    ADD CONSTRAINT entry_users_fk FOREIGN KEY (created_user) REFERENCES public.users (user_id);


--
-- Name: entrytags entrytags_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.entrytags
    ADD CONSTRAINT entrytags_entry_fk FOREIGN KEY (entry_id) REFERENCES public.entry (entry_id);


--
-- Name: entrytags entrytags_tags_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.entrytags
    ADD CONSTRAINT entrytags_tags_fk FOREIGN KEY (tag_id) REFERENCES public.tags (tag_id);


--
-- Name: entrytags entrytags_users_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.entrytags
    ADD CONSTRAINT entrytags_users_fk FOREIGN KEY (created_user) REFERENCES public.users (user_id);


--
-- Name: geometries geometries_datafiles_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.geometries
    ADD CONSTRAINT geometries_datafiles_fk FOREIGN KEY (datafile_id) REFERENCES public.datafiles (datafile_id);


--
-- Name: geometries geometries_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.geometries
    ADD CONSTRAINT geometries_entry_fk FOREIGN KEY (geometry_id) REFERENCES public.entry (entry_id);


--
-- Name: geometries geometries_geometrysubtype_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.geometries
    ADD CONSTRAINT geometries_geometrysubtype_fk FOREIGN KEY (geometrysubtype_id) REFERENCES public.geometrysubtypes (geometrysubtype_id);


--
-- Name: geometries geometries_geometrytype_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.geometries
    ADD CONSTRAINT geometries_geometrytype_fk FOREIGN KEY (geometrytype_id) REFERENCES public.geometrytypes (geometrytype_id);


--
-- Name: geometries geometries_platform_sensors_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.geometries
    ADD CONSTRAINT geometries_platform_sensors_fk FOREIGN KEY (sensor_platform_id) REFERENCES public.platforms (platform_id);


--
-- Name: geometries geometries_platform_subject_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.geometries
    ADD CONSTRAINT geometries_platform_subject_fk FOREIGN KEY (subject_platform_id) REFERENCES public.platforms (platform_id);


--
-- Name: geometries geometries_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.geometries
    ADD CONSTRAINT geometries_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public.privacies (privacy_id);


--
-- Name: geometries geometries_task_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.geometries
    ADD CONSTRAINT geometries_task_fk FOREIGN KEY (task_id) REFERENCES public.tasks (task_id);


--
-- Name: geometrysubtypes geometrysubtypes_geometrytype_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.geometrysubtypes
    ADD CONSTRAINT geometrysubtypes_geometrytype_fk FOREIGN KEY (geometrytype_id) REFERENCES public.geometrytypes (geometrytype_id);


--
-- Name: media media_datafiles_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.media
    ADD CONSTRAINT media_datafiles_fk FOREIGN KEY (datafile_id) REFERENCES public.datafiles (datafile_id);


--
-- Name: media media_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.media
    ADD CONSTRAINT media_entry_fk FOREIGN KEY (media_id) REFERENCES public.entry (entry_id);


--
-- Name: media media_mediatype_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.media
    ADD CONSTRAINT media_mediatype_fk FOREIGN KEY (mediatype_id) REFERENCES public.mediatypes (mediatype_id);


--
-- Name: media media_platform_source_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.media
    ADD CONSTRAINT media_platform_source_fk FOREIGN KEY (source_platform_id) REFERENCES public.platforms (platform_id);


--
-- Name: media media_platform_subject_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.media
    ADD CONSTRAINT media_platform_subject_fk FOREIGN KEY (subject_platform_id) REFERENCES public.platforms (platform_id);


--
-- Name: media media_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.media
    ADD CONSTRAINT media_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public.privacies (privacy_id);


--
-- Name: media media_sensor_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.media
    ADD CONSTRAINT media_sensor_fk FOREIGN KEY (sensor_id) REFERENCES public.sensors (sensor_id);


--
-- Name: narrativeentries narrativeentries_datafiles_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.narrativeentries
    ADD CONSTRAINT narrativeentries_datafiles_fk FOREIGN KEY (datafile_id) REFERENCES public.datafiles (datafile_id);


--
-- Name: narrativeentries narrativeentries_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.narrativeentries
    ADD CONSTRAINT narrativeentries_entry_fk FOREIGN KEY (narrativeentry_id) REFERENCES public.entry (entry_id);


--
-- Name: narrativeentries narrativeentries_entrytypes_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.narrativeentries
    ADD CONSTRAINT narrativeentries_entrytypes_fk FOREIGN KEY (entrytype_id) REFERENCES public.entrytypes (entrytype_id);


--
-- Name: narrativeentries narrativeentries_platform_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.narrativeentries
    ADD CONSTRAINT narrativeentries_platform_fk FOREIGN KEY (platform_id) REFERENCES public.platforms (platform_id);


--
-- Name: narrativeentries narrativeentries_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.narrativeentries
    ADD CONSTRAINT narrativeentries_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public.privacies (privacy_id);


--
-- Name: participation participation_platform_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.participation
    ADD CONSTRAINT participation_platform_fk FOREIGN KEY (platform_id) REFERENCES public.platforms (platform_id);


--
-- Name: participation participation_tasks_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.participation
    ADD CONSTRAINT participation_tasks_fk FOREIGN KEY (task_id) REFERENCES public.tasks (task_id);


--
-- Name: platforms platforms_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.platforms
    ADD CONSTRAINT platforms_entry_fk FOREIGN KEY (platform_id) REFERENCES public.entry (entry_id);


--
-- Name: platforms platforms_nationalities_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.platforms
    ADD CONSTRAINT platforms_nationalities_fk FOREIGN KEY (nationality_id) REFERENCES public.nationalities (nationality_id);


--
-- Name: platforms platforms_platforms_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.platforms
    ADD CONSTRAINT platforms_platforms_fk FOREIGN KEY (host_platform_id) REFERENCES public.platforms (platform_id);


--
-- Name: platforms platforms_platformtypes_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.platforms
    ADD CONSTRAINT platforms_platformtypes_fk FOREIGN KEY (platformtype_id) REFERENCES public.platformtypes (platformtype_id);


--
-- Name: sensors sensor_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT sensor_entry_fk FOREIGN KEY (sensor_id) REFERENCES public.entry (entry_id);


--
-- Name: sensors sensor_platforms_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT sensor_platforms_fk FOREIGN KEY (platform_id) REFERENCES public.platforms (platform_id);


--
-- Name: sensors sensor_sensortypes_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT sensor_sensortypes_fk FOREIGN KEY (sensortype_id) REFERENCES public.sensortypes (sensortype_id);


--
-- Name: state state_datafiles_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.state
    ADD CONSTRAINT state_datafiles_fk FOREIGN KEY (datafile_id) REFERENCES public.datafiles (datafile_id);


--
-- Name: state state_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.state
    ADD CONSTRAINT state_entry_fk FOREIGN KEY (state_id) REFERENCES public.entry (entry_id);


--
-- Name: state state_privacies_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.state
    ADD CONSTRAINT state_privacies_fk FOREIGN KEY (privacy_id) REFERENCES public.privacies (privacy_id);


--
-- Name: state state_sensors_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.state
    ADD CONSTRAINT state_sensors_fk FOREIGN KEY (sensor_id) REFERENCES public.sensors (sensor_id);


--
-- Name: tags tags_users_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_users_fk FOREIGN KEY (created_user) REFERENCES public.users (user_id);


--
-- Name: tasks tasks_entry_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_entry_fk FOREIGN KEY (task_id) REFERENCES public.entry (entry_id);


--
-- Name: tasks tasks_tasks_fk; Type: FK CONSTRAINT; Schema: public; Owner: tracstor_admin
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_tasks_fk FOREIGN KEY (parenttask_id) REFERENCES public.tasks (task_id);


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
-- Name: TABLE activations; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.activations TO tracstor_dev;


--
-- Name: TABLE changelog; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.changelog TO tracstor_dev;


--
-- Name: TABLE contacts; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.contacts TO tracstor_dev;


--
-- Name: TABLE datafiletypes; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.datafiletypes TO tracstor_dev;


--
-- Name: TABLE datafiles; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.datafiles TO tracstor_dev;


--
-- Name: TABLE entry; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.entry TO tracstor_dev;


--
-- Name: TABLE entrytags; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.entrytags TO tracstor_dev;


--
-- Name: TABLE entrytypes; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.entrytypes TO tracstor_dev;


--
-- Name: TABLE geometries; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.geometries TO tracstor_dev;


--
-- Name: TABLE geometrysubtypes; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.geometrysubtypes TO tracstor_dev;


--
-- Name: TABLE geometrytypes; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.geometrytypes TO tracstor_dev;


--
-- Name: TABLE media; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.media TO tracstor_dev;


--
-- Name: TABLE mediatypes; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.mediatypes TO tracstor_dev;


--
-- Name: TABLE narrativeentries; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.narrativeentries TO tracstor_dev;


--
-- Name: TABLE nationalities; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.nationalities TO tracstor_dev;


--
-- Name: TABLE participation; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.participation TO tracstor_dev;


--
-- Name: TABLE platformtypes; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.platformtypes TO tracstor_dev;


--
-- Name: TABLE platforms; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.platforms TO tracstor_dev;


--
-- Name: TABLE privacies; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.privacies TO tracstor_dev;


--
-- Name: TABLE sensortypes; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.sensortypes TO tracstor_dev;


--
-- Name: TABLE sensors; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.sensors TO tracstor_dev;


--
-- Name: TABLE state; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.state TO tracstor_dev;


--
-- Name: TABLE tabletypes; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.tabletypes TO tracstor_dev;


--
-- Name: TABLE tags; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.tags TO tracstor_dev;


--
-- Name: TABLE tasks; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.tasks TO tracstor_dev;


--
-- Name: TABLE users; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.users TO tracstor_dev;


--
-- Name: SEQUENCE users_user_id_seq; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON SEQUENCE public.users_user_id_seq TO tracstor_dev;


--
-- Name: TABLE test; Type: ACL; Schema: public; Owner: tracstor_admin
--

GRANT ALL ON TABLE public.test TO tracstor_dev;


--
-- PostgreSQL database dump complete
--

