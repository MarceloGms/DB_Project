CREATE TABLE consumer (
	person_id	 BIGSERIAL,
	person_username	 VARCHAR(512) NOT NULL,
	person_email	 VARCHAR(512) NOT NULL,
	person_password	 VARCHAR(512) NOT NULL,
	person_name	 VARCHAR(512) NOT NULL,
	person_birthdate DATE NOT NULL,
	PRIMARY KEY(person_id)
);

CREATE TABLE artist (
	artistic_name		 VARCHAR(512) NOT NULL,
	record_label_label_id	 BIGINT NOT NULL,
	administrator_person_id BIGINT NOT NULL,
	person_id		 BIGSERIAL,
	person_username	 VARCHAR(512) NOT NULL,
	person_email		 VARCHAR(512) NOT NULL,
	person_password	 VARCHAR(512) NOT NULL,
	person_name		 VARCHAR(512) NOT NULL,
	person_birthdate	 DATE NOT NULL,
	PRIMARY KEY(person_id)
);

CREATE TABLE administrator (
	person_id	 BIGSERIAL,
	person_username	 VARCHAR(512) NOT NULL,
	person_email	 VARCHAR(512) NOT NULL,
	person_password	 VARCHAR(512) NOT NULL,
	person_name	 VARCHAR(512) NOT NULL,
	person_birthdate DATE NOT NULL,
	PRIMARY KEY(person_id)
);

CREATE TABLE song (
	ismn			 BIGSERIAL,
	title		 VARCHAR(512) NOT NULL,
	genre		 VARCHAR(512) NOT NULL,
	release_date		 DATE NOT NULL,
	duration		 TIMESTAMP NOT NULL,
	record_label_label_id BIGINT NOT NULL,
	PRIMARY KEY(ismn)
);

CREATE TABLE playlist (
	playlist_id BIGSERIAL,
	name	 VARCHAR(512) NOT NULL,
	creator	 VARCHAR(512) NOT NULL,
	public	 BOOL NOT NULL,
	top_ten	 BOOL NOT NULL,
	PRIMARY KEY(playlist_id)
);

CREATE TABLE comment (
	comment_id		 BIGSERIAL,
	content			 VARCHAR(512) NOT NULL,
	comment_date		 DATE NOT NULL,
	consumer_person_id	 BIGINT,
	comment_comment_id	 BIGINT NOT NULL,
	comment_consumer_person_id BIGINT NOT NULL,
	song_ismn			 BIGINT NOT NULL,
	PRIMARY KEY(comment_id,consumer_person_id)
);

CREATE TABLE record_label (
	label_id BIGSERIAL,
	name	 VARCHAR(512) NOT NULL,
	PRIMARY KEY(label_id)
);

CREATE TABLE pre_paid_card (
	id_card		 BIGSERIAL,
	limit_date		 DATE NOT NULL,
	card_price		 SMALLINT NOT NULL,
	administrator_person_id BIGINT NOT NULL,
	PRIMARY KEY(id_card)
);

CREATE TABLE album (
	album_id		 BIGSERIAL,
	name			 VARCHAR(512) NOT NULL,
	genre		 VARCHAR(512) NOT NULL,
	publisher		 VARCHAR(512) NOT NULL,
	release_date		 DATE NOT NULL,
	record_label_label_id BIGINT NOT NULL,
	artist_person_id	 BIGINT NOT NULL,
	PRIMARY KEY(album_id)
);

CREATE TABLE subscription_transactions (
	subs_id			 BIGSERIAL,
	plan				 BOOL NOT NULL,
	date_start			 DATE NOT NULL,
	date_finish			 DATE NOT NULL,
	transactions_transaction_id	 BIGSERIAL NOT NULL,
	transactions_transaction_date DATE NOT NULL,
	PRIMARY KEY(subs_id)
);

CREATE TABLE activity (
	n_listens		 SMALLINT NOT NULL,
	listen_date	 DATE NOT NULL,
	song_ismn		 BIGINT,
	consumer_person_id BIGINT,
	PRIMARY KEY(song_ismn,consumer_person_id)
);

CREATE TABLE consumer_pre_paid_card (
	consumer_person_id	 BIGINT NOT NULL,
	pre_paid_card_id_card BIGINT,
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
	pre_paid_card_id_card		 BIGINT,
	PRIMARY KEY(subscription_transactions_subs_id,pre_paid_card_id_card)
);

CREATE TABLE song_album (
	song_ismn	 BIGINT,
	album_album_id BIGINT NOT NULL,
	PRIMARY KEY(song_ismn)
);

CREATE TABLE song_playlist (
	song_ismn		 BIGINT,
	playlist_playlist_id BIGINT,
	PRIMARY KEY(song_ismn,playlist_playlist_id)
);

ALTER TABLE consumer ADD UNIQUE (person_username);
ALTER TABLE artist ADD UNIQUE (artistic_name, person_username);
ALTER TABLE artist ADD CONSTRAINT artist_fk1 FOREIGN KEY (record_label_label_id) REFERENCES record_label(label_id);
ALTER TABLE artist ADD CONSTRAINT artist_fk2 FOREIGN KEY (administrator_person_id) REFERENCES administrator(person_id);
ALTER TABLE administrator ADD UNIQUE (person_username);
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

