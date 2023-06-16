CREATE TABLE consumer (
	person_id BIGINT,
	PRIMARY KEY(person_id)
);

CREATE TABLE artist (
	artistic_name		 VARCHAR(512) NOT NULL,
	administrator_person_id BIGINT NOT NULL,
	record_label_label_id	 BIGINT NOT NULL,
	person_id		 BIGINT,
	PRIMARY KEY(person_id)
);

CREATE TABLE administrator (
	person_id BIGINT,
	PRIMARY KEY(person_id)
);

CREATE TABLE person (
	id	 BIGSERIAL,
	username	 VARCHAR(512) NOT NULL,
	email	 VARCHAR(512) NOT NULL,
	password	 VARCHAR(512) NOT NULL,
	name	 VARCHAR(512) NOT NULL,
	birthdate DATE NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE song (
	ismn			 BIGSERIAL,
	title		 VARCHAR(512) NOT NULL,
	genre		 VARCHAR(512) NOT NULL,
	release_date		 DATE NOT NULL,
	duration		 SMALLINT NOT NULL,
	record_label_label_id BIGINT NOT NULL,
	PRIMARY KEY(ismn)
);

CREATE TABLE playlist (
	playlist_id BIGSERIAL,
	name	 VARCHAR(512) NOT NULL,
	creator	 VARCHAR(512) NOT NULL,
	public	 BOOL NOT NULL,
	top_ten	 BOOL NOT NULL DEFAULT FALSE,
	PRIMARY KEY(playlist_id)
);

CREATE TABLE comment (
    comment_id         BIGSERIAL,
    content             VARCHAR(512) NOT NULL,
    comment_date         DATE NOT NULL,
    consumer_person_id     BIGINT NOT NULL,
    comment_comment_id     BIGINT,
    comment_consumer_person_id BIGINT,
    song_ismn             BIGINT NOT NULL,
    PRIMARY KEY(comment_id,consumer_person_id)
);

CREATE TABLE record_label (
	label_id BIGSERIAL,
	name	 VARCHAR(512) NOT NULL,
	PRIMARY KEY(label_id)
);

CREATE TABLE pre_paid_card (
	id_card		 VARCHAR(512),
	limit_date		 DATE NOT NULL,
	card_price		 SMALLINT NOT NULL,
	administrator_person_id BIGINT NOT NULL,
	PRIMARY KEY(id_card)
);

CREATE TABLE album (
	album_id		 BIGSERIAL,
	name			 VARCHAR(512) NOT NULL,
	genre		 VARCHAR(512) NOT NULL,
	release_date		 DATE NOT NULL,
	record_label_label_id BIGINT NOT NULL,
	artist_person_id	 BIGINT NOT NULL,
	PRIMARY KEY(album_id)
);

CREATE TABLE subscription_transactions (
	subs_id			 BIGSERIAL,
	plan				 VARCHAR(512) NOT NULL,
	date_start			 DATE NOT NULL,
	date_finish			 DATE NOT NULL,
	transactions_transaction_id	 BIGSERIAL NOT NULL,
	transactions_transaction_date DATE NOT NULL,
	PRIMARY KEY(subs_id)
);

CREATE TABLE activity (
	id		 BIGSERIAL,
	n_listens		 SMALLINT NOT NULL,
	listen_date	 DATE NOT NULL,
	song_ismn		 BIGINT,
	consumer_person_id BIGINT,
	PRIMARY KEY(id,song_ismn,consumer_person_id)
);

CREATE TABLE consumer_pre_paid_card (
	consumer_person_id	 BIGINT NOT NULL,
	pre_paid_card_id_card VARCHAR(512),
	PRIMARY KEY(pre_paid_card_id_card)
);

CREATE TABLE consumer_subscription_transactions (
	consumer_person_id		 BIGINT,
	subscription_transactions_subs_id BIGINT,
	PRIMARY KEY(consumer_person_id,subscription_transactions_subs_id)
);

CREATE TABLE artist_song (
	artist_person_id BIGINT,
	song_ismn	 BIGINT,
	PRIMARY KEY(artist_person_id,song_ismn)
);

CREATE TABLE consumer_playlist (
	consumer_person_id	 BIGINT,
	playlist_playlist_id BIGINT,
	PRIMARY KEY(consumer_person_id,playlist_playlist_id)
);

CREATE TABLE subscription_transactions_pre_paid_card (
	subscription_transactions_subs_id BIGINT,
	pre_paid_card_id_card		 VARCHAR(512),
	PRIMARY KEY(subscription_transactions_subs_id,pre_paid_card_id_card)
);

CREATE TABLE song_album (
	song_ismn	 BIGINT,
	album_album_id BIGINT,
	PRIMARY KEY(song_ismn,album_album_id)
);

CREATE TABLE song_playlist (
	song_ismn		 BIGINT,
	playlist_playlist_id BIGINT,
	PRIMARY KEY(song_ismn,playlist_playlist_id)
);

ALTER TABLE consumer ADD CONSTRAINT consumer_fk1 FOREIGN KEY (person_id) REFERENCES person(id);
ALTER TABLE artist ADD UNIQUE (artistic_name);
ALTER TABLE artist ADD CONSTRAINT artist_fk1 FOREIGN KEY (administrator_person_id) REFERENCES administrator(person_id);
ALTER TABLE artist ADD CONSTRAINT artist_fk2 FOREIGN KEY (record_label_label_id) REFERENCES record_label(label_id);
ALTER TABLE artist ADD CONSTRAINT artist_fk3 FOREIGN KEY (person_id) REFERENCES person(id);
ALTER TABLE administrator ADD CONSTRAINT administrator_fk1 FOREIGN KEY (person_id) REFERENCES person(id);
ALTER TABLE person ADD UNIQUE (username);
ALTER TABLE song ADD CONSTRAINT song_fk1 FOREIGN KEY (record_label_label_id) REFERENCES record_label(label_id);
ALTER TABLE comment ADD CONSTRAINT comment_fk1 FOREIGN KEY (consumer_person_id) REFERENCES consumer(person_id);
ALTER TABLE comment ADD CONSTRAINT comment_fk2 FOREIGN KEY (comment_comment_id, comment_consumer_person_id) REFERENCES comment(comment_id, consumer_person_id);
ALTER TABLE comment ADD CONSTRAINT comment_fk3 FOREIGN KEY (song_ismn) REFERENCES song(ismn);
ALTER TABLE record_label ADD UNIQUE (name);
ALTER TABLE pre_paid_card ADD CONSTRAINT pre_paid_card_fk1 FOREIGN KEY (administrator_person_id) REFERENCES administrator(person_id);
ALTER TABLE album ADD CONSTRAINT album_fk1 FOREIGN KEY (record_label_label_id) REFERENCES record_label(label_id);
ALTER TABLE album ADD CONSTRAINT album_fk2 FOREIGN KEY (artist_person_id) REFERENCES artist(person_id);
ALTER TABLE subscription_transactions ADD UNIQUE (transactions_transaction_id);
ALTER TABLE activity ADD CONSTRAINT activity_fk1 FOREIGN KEY (song_ismn) REFERENCES song(ismn);
ALTER TABLE activity ADD CONSTRAINT activity_fk2 FOREIGN KEY (consumer_person_id) REFERENCES consumer(person_id);
ALTER TABLE consumer_pre_paid_card ADD CONSTRAINT consumer_pre_paid_card_fk1 FOREIGN KEY (consumer_person_id) REFERENCES consumer(person_id);
ALTER TABLE consumer_pre_paid_card ADD CONSTRAINT consumer_pre_paid_card_fk2 FOREIGN KEY (pre_paid_card_id_card) REFERENCES pre_paid_card(id_card);
ALTER TABLE consumer_subscription_transactions ADD CONSTRAINT consumer_subscription_transactions_fk1 FOREIGN KEY (consumer_person_id) REFERENCES consumer(person_id);
ALTER TABLE consumer_subscription_transactions ADD CONSTRAINT consumer_subscription_transactions_fk2 FOREIGN KEY (subscription_transactions_subs_id) REFERENCES subscription_transactions(subs_id);
ALTER TABLE artist_song ADD CONSTRAINT artist_song_fk1 FOREIGN KEY (artist_person_id) REFERENCES artist(person_id);
ALTER TABLE artist_song ADD CONSTRAINT artist_song_fk2 FOREIGN KEY (song_ismn) REFERENCES song(ismn);
ALTER TABLE consumer_playlist ADD CONSTRAINT consumer_playlist_fk1 FOREIGN KEY (consumer_person_id) REFERENCES consumer(person_id);
ALTER TABLE consumer_playlist ADD CONSTRAINT consumer_playlist_fk2 FOREIGN KEY (playlist_playlist_id) REFERENCES playlist(playlist_id);
ALTER TABLE subscription_transactions_pre_paid_card ADD CONSTRAINT subscription_transactions_pre_paid_card_fk1 FOREIGN KEY (subscription_transactions_subs_id) REFERENCES subscription_transactions(subs_id);
ALTER TABLE subscription_transactions_pre_paid_card ADD CONSTRAINT subscription_transactions_pre_paid_card_fk2 FOREIGN KEY (pre_paid_card_id_card) REFERENCES pre_paid_card(id_card);
ALTER TABLE song_album ADD CONSTRAINT song_album_fk1 FOREIGN KEY (song_ismn) REFERENCES song(ismn);
ALTER TABLE song_album ADD CONSTRAINT song_album_fk2 FOREIGN KEY (album_album_id) REFERENCES album(album_id);
ALTER TABLE song_playlist ADD CONSTRAINT song_playlist_fk1 FOREIGN KEY (song_ismn) REFERENCES song(ismn);
ALTER TABLE song_playlist ADD CONSTRAINT song_playlist_fk2 FOREIGN KEY (playlist_playlist_id) REFERENCES playlist(playlist_id);

