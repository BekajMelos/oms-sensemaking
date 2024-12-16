#!/bin/bash
#
# This script is designed to configure the SNS+SQS fanout for the OMSB Events.
# A single SNS Topic is created for OMSB Events. Then multiple SQS Queues
# are created and subscribed to the SNS Topic for messages to be processed by
# OMSB Workers.
#
#    SNS Topic                SQS Queues                   OMSB Workers
#
# |-------------|        |-------------------|        |----------------------|
# |             |------->| resolutionTrigger |------->|  Resolution Worker   |
# |             |        |-------------------|        |----------------------|
# | OMSB Events |
# |             |        |-------------------|        |----------------------|
# |             |------->|   guideEvents    |------->| External Sync Worker |
# |-------------|        |-------------------|        |----------------------|
#
set -eo pipefail
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

AWS_COMMAND=${AWS_COMMAND:-awslocal}
AWS_ENDPOINT_URL=${AWS_ENDPOINT_URL}
AWS_COMMAND_OPTS=""
if [ "${AWS_ENDPOINT_URL}" ]; then
  AWS_COMMAND_OPTS="--endpoint-url ${AWS_ENDPOINT_URL}"
fi

OMSB_EVENTS_TOPIC=${OMSB_EVENTS_TOPIC:-"omsbEvents"}
OMSB_SQS_QUEUES=${OMSB_SQS_QUEUE_CONFIG:-resolutionTrigger,guideTrigger,essTrigger,aorTrigger,geoSensemakerTrigger,attributeTrigger}
OMSB_TEST_MESSAGE=${OMSB_TEST_MESSAGE}

# Create the SNS Topic
echo "Creating SNS Topic ${OMSB_EVENTS_TOPIC}..."
topic_arn=$(
  ${AWS_COMMAND} sns create-topic ${AWS_COMMAND_OPTS} \
    --output text \
    --name ${OMSB_EVENTS_TOPIC} \
    --attributes DisplayName="${OMSB_EVENTS_TOPIC}",FifoTopic=false
)
echo "SNS Topic ARN: ${topic_arn}"

# Create each SQS Queue. From the URL, get the Queue ARN to subscribe to
# the SNS Topic.
for queue_name in ${OMSB_SQS_QUEUES//,/ }; do
  if [ -f "${SCRIPT_DIR}/${queue_name}_attributes.json" ] && [ -f "${SCRIPT_DIR}/${queue_name}_subscription.json" ]; then


    echo "Creating SQS Queue ${queue_name}..."
    queue_url=$(
      ${AWS_COMMAND} sqs create-queue ${AWS_COMMAND_OPTS} \
        --output text \
        --queue-name ${queue_name} \
        --attributes file://${SCRIPT_DIR}/${queue_name}_attributes.json
    )
    echo "SQS Queue URL: ${queue_url}"

    queue_arn=$(
      ${AWS_COMMAND} sqs get-queue-attributes ${AWS_COMMAND_OPTS} \
        --output text \
        --queue-url ${queue_url} \
        --attribute-names QueueArn | awk '{ print $2 }'
    )
    echo "SQS Queue ARN: ${queue_arn}"

    echo "Updating SQS Policy..."
    queue_policy=$(
      TOPIC_ARN=${topic_arn} QUEUE_ARN=${queue_arn} \
      envsubst < ${SCRIPT_DIR}/queue_policy.json.tpl
    )
    ${AWS_COMMAND} sqs set-queue-attributes \
      --queue-url ${queue_url} \
      --attributes "Policy='${queue_policy}'"

    echo "Subscribing ${queue_name} queue to ${OMSB_EVENTS_TOPIC} topic..."
    ${AWS_COMMAND} sns subscribe ${AWS_COMMAND_OPTS} \
      --output text \
      --topic-arn ${topic_arn} \
      --protocol sqs \
      --notification-endpoint ${queue_arn} \
      --attributes file://${SCRIPT_DIR}/${queue_name}_subscription.json

  else
    echo "Failed to create SQS Queue ${queue_name}..."
    echo "Missing ${queue_name}_attributes.json and ${queue_name}_subscription.json files..."
  fi
done

exit 0
