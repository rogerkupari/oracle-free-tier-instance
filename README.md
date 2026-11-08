# Oracle Free Tier Instance

A script to create a Free Tier Compute Instance in Oracle Cloud. Runs in a Docker-based environment, making it easy to deploy across different systems. Includes Telegram monitoring.

## Features

- OCI CLI API integration
- Telegram monitoring (`telly`)

## Requirements

- Docker Engine
- Oracle Cloud Free Tier account
- Telegram account

## Setup

1. Create your environment configuration file:

   ```bash
   cp .env.example .env
   ```

### Telegram Configuration

1. Send `/newbot` to [@BotFather](https://t.me/BotFather) and follow the instructions to create a bot.
2. Copy the HTTP API token provided by BotFather into `TELEGRAM_BOT_TOKEN` in your `.env` file.
3. Send `/start` to your newly created bot.
4. Send `/start` to [@userinfobot](https://t.me/userinfobot) and copy your `id` into `TELEGRAM_CHAT_ID` in your `.env` file.
5. Generate a secure API key using the following command:

   ```bash
   openssl rand -hex 32
   ```

6. Copy the generated value into `GATEWAY_API_KEY` in your `.env` file.

### Oracle API Keys (Linux)

1. Generate a private key:

   ```bash
   openssl genrsa -out oci_api_key.pem 2048
   ```

2. Generate the corresponding public key:

   ```bash
   openssl rsa -pubout -in oci_api_key.pem -out oci_api_key_public.pem
   ```

3. Save the key files in `OCI/.oci/keys/api/`, or specify the correct path using `OCI_CLI_KEY_FILE` in your `.env` file.

   **Important:** Set the private key file permissions to `600`.

4. Add your public key in Oracle Cloud:
   - Open **User Settings**.
   - Navigate to **Tokens and Keys**.
   - Select **Add API Key**.

5. Copy the configuration details provided by Oracle Cloud and enter the corresponding values in your `.env` file.

### Remaining Environment Configuration

- Follow the instructions and comments provided in the `.env` file to configure the remaining variables.

### Docker Setup

1. Install Docker Engine.
2. Build the images and start the containers:

   ```bash
   docker compose up -d --build
   ```

3. Validate your Oracle Cloud configuration:

   ```bash
   docker exec -it oci oci iam user list
   ```

4. Optionally, test the Telegram connection from the OCI container:

   ```bash
   docker exec -it oci telly it works
   ```

5. Optionally, test the Telegram connection from the Telegram Gateway container:

   ```bash
   docker exec -it telegram-gateway telly it works
   ```

6. Start the OCI service:

   ```bash
   docker exec -d oci bash -c 'bash /workspace/OCI/scripts/make_instance.sh > $SOCI_LOG_FILE 2>&1'
   ```

## Monitoring

The service is monitored through Telegram. The following events trigger notifications:

- **Inactivity:** If the log file has not been updated for 5 minutes, a Telegram notification is sent indicating that the service has stopped.
- **Unhandled errors:** If an unhandled error occurs, a Telegram error notification is sent and the OCI service is stopped.
- **Successful instance creation:** Once the instance has been successfully created, the OCI service stops automatically.

### Telegram Commands

- Send `status` to the Telegram bot to receive the latest line from the OCI log file.

### Logs

To view the OCI service logs:

```bash
docker exec -it oci bash -c 'cat "$SOCI_LOG_FILE"'
```

## Commands

### Docker

| Command | Description |
|---|---|
| `docker compose up -d --build` | Build images and start containers. |
| `docker compose up -d` | Start containers. |
| `docker compose down` | Stop and remove containers. |
| `docker system prune -a --volumes` | Remove unused Docker resources. ⚠️ Use with caution |

### OCI

| Command | Description |
|---|---|
| `docker exec -it oci bash` | Open a terminal inside the OCI container. |
| `docker exec -d oci bash -c 'bash /workspace/OCI/scripts/make_instance.sh > $SOCI_LOG_FILE 2>&1'` | Start the OCI service. |
| `docker exec -it oci bash -c 'tail -n 1 "$SOCI_LOG_FILE"'` | Display the last line of the OCI log file. |
| `docker exec -it oci bash -c 'tail "$SOCI_ERR_LOG_FILE"'` | Display the OCI error log. |
| `docker exec -it oci oci iam user list` | Verify the OCI configuration. |
| `docker exec -it oci telly it works` | Test the Telegram connection from the OCI container. |

### Telegram

| Command | Description |
|---|---|
| `docker exec -it telegram-gateway bash` | Open a terminal inside the Telegram Gateway container. |
| `docker logs telegram-gateway` | Display the Telegram Gateway logs. |
| `docker exec -it telegram-gateway telly it works` | Test the Telegram connection from the Telegram Gateway container. |
