CREATE TABLE version_datafile (
    id CHAR(32) NOT NULL,
    version VARCHAR(32),
    datafile VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "uq_version_datafile_version_datafile"  UNIQUE (version, datafile),
    CONSTRAINT "pk_version_datafile" PRIMARY KEY (id)
);

INSERT INTO version_datafile (id, version, datafile) VALUES ('1', 'd5d740c76aa3', 'nisida_example.txt');
INSERT INTO version_datafile (id, version, datafile) VALUES ('2', 'd5d740c76aa3', 'nisida_invalid_header_line.txt');
INSERT INTO version_datafile (id, version, datafile) VALUES ('3', 'd5d740c76aa3', 'nisida_split_narrative.txt');