{
  "Statement": [
    {
      "Sid": "OMSB Allow SNS Messages",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "${QUEUE_ARN}",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "${TOPIC_ARN}"
        }
      }
    }
  ]
}
