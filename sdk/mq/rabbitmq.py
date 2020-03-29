import time
import pika
import pickle


class RabbitMQClient:
    def __init__(self):
        self._connection = None
        self._channel = None
        self._config = None

    def init(self, host, port, username, password, virtual_host, **kwargs):
        assert isinstance(host, str)
        assert isinstance(port, int)
        assert isinstance(username, str)
        assert isinstance(password, str)
        assert isinstance(virtual_host, str)

        self._config = dict(
            host=host,
            port=port,
            username=username,
            password=password,
            virtual_host=virtual_host,
        )
        self._init_connection()

    def _init_connection(self):
        self._connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self._config["host"],
                port=self._config["port"],
                credentials=pika.PlainCredentials(
                    username=self._config["username"], password=self._config["password"]),
                virtual_host=self._config["virtual_host"],
            )
        )
        self._channel = self._connection.channel()

    def queue_declare(self, queue):
        assert isinstance(queue, str)
        if self._channel is None:
            raise ValueError("Not initialized")
        self._channel.queue_declare(queue=queue)

    def queue_delete(self, queue):
        assert isinstance(queue, str)
        if self._channel is None:
            raise ValueError("Not initialized")
        self._channel.queue_delete(queue=queue)

    def queue_purge(self, queue):
        assert isinstance(queue, str)
        if self._channel is None:
            raise ValueError("Not initialized")
        self._channel.queue_purge(queue=queue)

    def get(self, queue):
        assert isinstance(queue, str)

        retry_count = 0
        pickled = None
        while retry_count < 5:
            try:
                if self._connection.is_closed:
                    self._init_connection()
                    retry_count += 1

                _, _, pickled = self._channel.basic_get(queue, auto_ack=True)
                break
            except Exception as e:
                print(e)
                retry_count += 1
                time.sleep(0.1)
                continue

        if retry_count == 5:
            raise ValueError("Connection error with AMQP")

        if pickled is None:
            return None
        else:
            return pickle.loads(pickled)

    def publish(self, queue, data):
        assert isinstance(data, dict)

        is_success = False
        retry_count = 0
        while retry_count < 5:
            try:
                if self._connection.is_closed:
                    self._init_connection()
                    retry_count += 1

                self._channel.basic_publish(
                    exchange="",
                    routing_key=queue,
                    body=pickle.dumps(data, pickle.HIGHEST_PROTOCOL))
                is_success = True
                break
            except:
                retry_count += 1
                time.sleep(0.5)
                continue
        if not is_success:
            raise ValueError("Connection error with AMQP")
