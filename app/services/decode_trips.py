from typing import Optional
import logging
import os
import time
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class PostgresConnector:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PostgresConnector, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):

        load_dotenv()
        try:
            self.db_name = os.environ["PG_DB_NAME"]
            self.db_user = os.environ["PG_USER"]
            self.db_password = os.environ["PG_PASSWORD"]
            self.db_host = os.environ.get("PG_HOST", "localhost")
            self.db_port = os.environ.get("PG_PORT", "5432")

        except KeyError as e:
            raise EnvironmentError(
                f"Missing required environment variable: {e}. Check your shell environment or .env file."
            ) from e

        self.connect()

    def connect(self):
        if self._connection is not None:
            try:
                self._connection.close()
                self._connection = None
            except OperationalError:
                pass

        max_retries = 5
        retry_delay = 2  # seconds
        for attempt in range(1, max_retries + 1):
            try:
                self._connection = psycopg2.connect(
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password,
                    host=self.db_host,
                    port=self.db_port,
                )
                logger.info(
                    f"Database connected successfully to {self.db_host}:{self.db_port}/{self.db_name}"
                )
                return
            except OperationalError as e:
                if attempt < max_retries:
                    logger.info(
                        f"Connection attempt {attempt}/{max_retries} failed, retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                else:
                    logger.error(f"All {max_retries} connection attempts failed: {e}")
                    self._connection = None
                    raise

    def close(self):
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
                logger.info("Database connection closed.")
            except OperationalError as e:
                logger.error(f"Error closing connection: {e}")


class TripDecoder:
    def __init__(self):
        self.db = PostgresConnector()
    
    def get_route_name_from_trip(self, gtfs_trip_id: str) -> Optional[str]:
        """
        ترجع اسم الراوت بناءً على gtfs_trip_id
        """
        query = """
            SELECT r.name
            FROM trip t
            JOIN route r ON t.route_id = r.route_id
            WHERE t.gtfs_trip_id = %s
            LIMIT 1
        """
        conn = self.db._connection
        if conn is None:
            self.db.connect()
            conn = self.db._connection

        cur = None
        try:
            cur = conn.cursor()
            cur.execute(query, (gtfs_trip_id,))
            row = cur.fetchone()
            if row:
                return row[0]  # route_name
            return None
        except Exception as e:
            print(f"Error fetching route_name for gtfs_trip_id={gtfs_trip_id}: {e}")
            return None
        finally:
            if cur:
                cur.close()


    def filter_sort(self, route_response):
        journeys = route_response.get("journeys", [])
        journeys_sorted = sorted(
        journeys,
        key=lambda j: (
        j.get("costs", {}).get("walk", 0),  # أقل مشي أولاً
        j.get("costs", {}).get("money", 0)  # ثم أقل سعر
           )
                 )
        journeys_top = journeys_sorted[:5]
        return journeys_top


    def decode_path(self, path: list) -> list:
        """
        تحول list من gtfs_trip_ids ل list من route_names جاهزة للمستخدم
        """
        readable_path = []
        for trip_id in path:
            route_name = self.get_route_name_from_trip(trip_id)
            readable_path.append(route_name or "(خط غير معروف)")
        return readable_path





