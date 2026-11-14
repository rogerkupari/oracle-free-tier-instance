#!/bin/bash


IFS=',' read -ra AVAILABILITY_DOMAINS <<< "$SOCI_AVAILABILITY_DOMAINS"

> $SOCI_LOG_FILE
> $SOCI_ERR_LOG_FILE


telly OCI service script started
while true; do
        for AVAILABILITY_DOMAIN in "${AVAILABILITY_DOMAINS[@]}"; do
            echo "$(date): Attempting to create instance in: $AVAILABILITY_DOMAIN"
         # ---------------------- <UPDATE AS NECESSARY> ------------------------
            oci compute instance launch \
                --availability-domain "$AVAILABILITY_DOMAIN" \
                --compartment-id "$SOCI_COPARTMENT" \
                --shape "$SOCI_INSTANCE_SHAPE" \
                --subnet-id "$SOCI_SUBNET" \
                --assign-private-dns-record $SOCI_PRIVATE_DNS \
                --assign-public-ip $SOCI_PUBLIC_IP \
                --availability-config '{"recovery_action": "RESTORE_INSTANCE"}' \
                --display-name "$SOCI_INSTANCE_NAME" \
                --instance-options '{"are_legacy_imds_endpoints_disabled": false}' \
                --shape-config "{\"ocpus\": $SOCI_OCPUS, \"memoryInGBs\": $SOCI_RAM_GB}" \
                --image-id "$SOCI_IMAGE" \
                --boot-volume-size-in-gbs "$SOCI_BOOT_VOLUME_GB" \
                --ssh-authorized-keys-file "$SOCI_INSTANCE_PUBLIC_KEY" \
                --wait-for-state RUNNING \
                --connection-timeout $SOCI_CONN_TIMEOUT_S \
                2> $SOCI_ERR_LOG_FILE

            if [ $? -eq 0 ]; then
                echo "$(date): Instance created successfully in $AVAILABILITY_DOMAIN."
                telly Instance created, stopping the service
                exit 0
            elif grep -qi "OutOfCapacity\|OutOfHostCapacity\|out of host capacity" $SOCI_ERR_LOG_FILE; then
                 echo "$(date): Out of Capacity, trying another AD"
                 sleep 100
            elif grep -qi "TooManyRequests" $SOCI_ERR_LOG_FILE; then
                 telly TooManyRequests...
                 echo "$(date): Rate-limit, waiting..."
                 sleep 300
            else
                 echo "$(date): Unhandled error, stopping the service"
                 cat $SOCI_ERR_LOG_FILE
                 telly Unhandled error, stopping the service
                 exit 1
            fi
        done
        file_size=`du -b $SOCI_LOG_FILE | tr -s '\t' ' ' | cut -d' ' -f1`
                if [ $file_size -gt $SOCI_MAX_LOG_SIZE ];then
                        > $SOCI_LOG_FILE
                fi

done
