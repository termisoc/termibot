DROP TABLE IF EXISTS karma CASCADE;
CREATE TABLE karma (item character varying(255) NOT NULL, time timestamp with time zone NOT NULL, direction smallint NOT NULL, reason text);
CREATE INDEX karma_direction ON karma USING btree (direction);
CREATE INDEX karma_item ON karma USING btree (item);
CREATE INDEX karma_item_like ON karma USING btree (item varchar_pattern_ops);

DROP TABLE IF EXISTS karma_maps CASCADE;
CREATE TABLE karma_maps (from_name character varying(255) NOT NULL, to_name character varying(255) NOT NULL);

DROP TABLE IF EXISTS URLS CASCADE;
CREATE TABLE urls (url text NOT NULL, posted timestamp with time zone NOT NULL, short_url text, nick text NOT NULL);
