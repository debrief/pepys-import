CREATE TABLE pepys."version_datafile" (
    id INTEGER NOT NULL,
    version CHARACTER VARYING(32),
    datafile CHARACTER VARYING(150),
    created_at TIMESTAMP DEFAULT NOW()::TIMESTAMP
);

ALTER TABLE ONLY pepys."version_datafile"
    ADD CONSTRAINT "pk_version_datafile" PRIMARY KEY (id);
ALTER TABLE ONLY pepys."version_datafile"
    ADD CONSTRAINT "uq_version_datafile_version_datafile" UNIQUE (version, datafile);

INSERT INTO pepys."version_datafile" (id, version, datafile) VALUES ('1', 'b311affac706', 'nisida_example.txt');
INSERT INTO pepys."version_datafile" (id, version, datafile) VALUES ('2', 'b311affac706', 'nisida_invalid_header_line.txt');
INSERT INTO pepys."version_datafile" (id, version, datafile) VALUES ('3', 'b311affac706', 'nisida_split_narrative.txt');