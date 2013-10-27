create table subreddits ( name text, last_fetched text );
create table threads ( id text, album_id text, deletehash text );
create index thread_id_index on threads ( id );
create index subreddit_name_index on subreddits ( name );
