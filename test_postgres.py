from testing.postgresql import Postgresql

print("Testing Postgres")
postgres = Postgresql(
    database="test",
    host="localhost",
    user="postgres",
    password="postgres",
    port=55527,
)
