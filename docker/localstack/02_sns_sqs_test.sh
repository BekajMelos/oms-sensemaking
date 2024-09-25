#!/bin/bash
#
# This script tests the SNS Topic and SQS Queues created in the bootstrap
# script.
#
# TODO: Note that this is assuming the default filtering on the message
#  attributes having key1=value1. We should update this test if and when
#  the filtering has been updated.
#
set -eo pipefail

AWS_COMMAND=${AWS_COMMAND:-awslocal}
AWS_ENDPOINT_URL=${AWS_ENDPOINT_URL}
AWS_COMMAND_OPTS=""
if [ "${AWS_ENDPOINT_URL}" ]; then
  AWS_COMMAND_OPTS="--endpoint-url ${AWS_ENDPOINT_URL}"
fi

OMSB_EVENTS_TOPIC=${OMSB_EVENTS_TOPIC:-"omsbEvents"}
OMSB_TEST_MESSAGE=${OMSB_TEST_MESSAGE}

if [ ! "${OMSB_TEST_MESSAGE}" ]; then
  echo "Missing test message. Exiting..."
  exit 0
fi

# List out resources - Topics, Queues, and Subscriptions - to verify
# that the fanout has been configured as desired.
${AWS_COMMAND} sns list-topics ${AWS_COMMAND_OPTS}
${AWS_COMMAND} sqs list-queues ${AWS_COMMAND_OPTS}
${AWS_COMMAND} sns list-subscriptions ${AWS_COMMAND_OPTS}

# Create the SNS Topic. Use content-based deduplication to prevent
# duplicate messages.
topic_arn=$(
  ${AWS_COMMAND} sns list-topics ${AWS_COMMAND_OPTS} \
    --output text | awk '{ print $2 }'
)
echo "SNS Topic ARN: ${topic_arn}"

# Create a test message and publish to the SNS Topic
echo "Publishing a test message to the ${OMSB_EVENTS_TOPIC} topic..."
${AWS_COMMAND} sns publish ${AWS_COMMAND_OPTS} \
  --topic ${topic_arn} \
  --message "${OMSB_TEST_MESSAGE}" \
  --message-attributes '{"objectType":{"DataType":"String","StringValue":"NODE"},"eventType":{"DataType":"String","StringValue":"CREATE"}}'

# Receive, "process," and delete the test message from each SQS Queue
for queue_url in $( ${AWS_COMMAND} sqs list-queues ${AWS_COMMAND_OPTS} | jq -rc '.QueueUrls[]' ); do
  echo "Receiving test message from ${queue_url}..."
  test_message=$(
    ${AWS_COMMAND} sqs receive-message ${AWS_COMMAND_OPTS} \
      --queue-url ${queue_url} \
      --attribute-names All
  )
  echo "Test message: ${test_message}"

  if [ -n "${test_message}" ]; then
    echo "Acknowledged test message from ${queue_url}..."
    echo "Deleting test message from ${queue_url}..."

    receipt_handle=$( echo ${test_message} | jq -r .Messages[0].ReceiptHandle )
    ${AWS_COMMAND} sqs delete-message ${AWS_COMMAND_OPTS} \
      --queue-url ${queue_url} \
      --receipt-handle ${receipt_handle}
  else
    echo "No message received on queue ${queue_url}..."
  fi
done

exit 0
