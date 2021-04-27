# postgresql-proxy

### Setting up networking between proxy and client space  


#### In proxy space  

`cf map-route postgresql-proxy apps.internal --hostname data-workspace-datasets-for-<client>`

`cf delete-route london.cloudapps.digital --hostname postgresql-proxy`

#### In client space

`cf add-network-policy <client_app> --destination-app postgresql-proxy -s <proxy_space> --protocol tcp --port 5432`