from datetime import datetime
from aws_cdk import core

def add_tags(cdk_construct, user_email: str, client='none', project='internal', more_tags=None) -> None:
    tags = {'CreatedBy': user_email,
            'CreatedOn': datetime.today().strftime('%Y-%m-%d'),
            'Client': client,
            'Project': project}

    if more_tags:
        tags.update(more_tags)

    for k, v in tags.items():
        core.Tags.of(cdk_construct).add(k, v)