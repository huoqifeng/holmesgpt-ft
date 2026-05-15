# Incident: High Memory Usage

# Prompt
The cluster is experiencing high memory usage. Identify the cause and implement a solution.

# Investigation Steps

Let's first check the overall cluster resource usage:

```bash
kubectl top nodes
```

```text
NAME             CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
master-node      450m         22%    8.2Gi           52%
worker-node-1    1200m        60%    14.8Gi          93%
worker-node-2    800m         40%    12.1Gi          76%
```

Worker node 1 is showing 93% memory usage. Let's check which pods are consuming the most memory:

```bash
kubectl top pods --all-namespaces --sort-by=memory
```

```text
NAMESPACE     NAME                                   CPU(cores)   MEMORY(bytes)
production    memory-hog-app-7d9c4f8b5-2xq9w         150m         6.8Gi
production    web-app-5f7b9c2d1-abc12                200m         2.1Gi
production    database-0                             300m         1.9Gi
monitoring    prometheus-server-7b8d9f2a1-cd34e     250m         1.5Gi
```

The memory-hog-app pod is consuming 6.8Gi of memory. Let's get more details about this pod:

```bash
kubectl describe pod memory-hog-app-7d9c4f8b5-2xq9w -n production
```

```text
Name:         memory-hog-app-7d9c4f8b5-2xq9w
Namespace:    production
Priority:     0
Node:         worker-node-1/10.0.1.4
Start Time:   Mon, 15 May 2026 09:15:23 +0000
Labels:       app=memory-hog-app
              pod-template-hash=7d9c4f8b5
Annotations:  <none>
Status:       Running
IP:           10.244.1.8
IPs:
  IP:  10.244.1.8
Containers:
  memory-hog-app:
    Container ID:   containerd://def456ghi789
    Image:          memory-hog-app:latest
    Image ID:       docker.io/library/memory-hog-app@sha256:abc123
    Port:           8080/TCP
    Host Port:      0/TCP
    State:          Running
      Started:      Mon, 15 May 2026 09:15:24 +0000
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     500m
      memory:  8Gi
    Requests:
      cpu:     100m
      memory:  128Mi
    Environment:
      MEMORY_MODE:  unlimited
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-xyz (ro)
```

Let's check the logs to understand what this application is doing:

```bash
kubectl logs memory-hog-app-7d9c4f8b5-2xq9w -n production
```

```text
2026-05-15 09:15:25 INFO Starting memory allocation service...
2026-05-15 09:15:25 INFO Allocating memory blocks...
2026-05-15 09:15:26 INFO Memory block 1 allocated: 1024MB
2026-05-15 09:15:26 INFO Memory block 2 allocated: 1024MB
...
2026-05-15 09:15:32 INFO Memory block 7 allocated: 1024MB
2026-05-15 09:15:32 INFO Total memory allocated: 7168MB
2026-05-15 09:15:32 INFO Memory allocation complete. Holding memory...
```

The application is intentionally allocating large amounts of memory. Let's check if there are any resource limits defined in the deployment:

```bash
kubectl get deployment memory-hog-app -n production -o yaml
```

```text
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-hog-app
  namespace: production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: memory-hog-app
  template:
    metadata:
      labels:
        app: memory-hog-app
    spec:
      containers:
      - name: memory-hog-app
        image: memory-hog-app:latest
        ports:
        - containerPort: 8080
        env:
        - name: MEMORY_MODE
          value: unlimited
        resources:
          limits:
            cpu: 500m
            memory: 8Gi
          requests:
            cpu: 100m
            memory: 128Mi
```

# Resolution
The memory-hog-app deployment has a memory limit of 8Gi but it's consuming most of that. We have several options:

1. Reduce the memory limit to force the application to use less memory
2. Scale down the application if it's not critical
3. Add resource quotas to the namespace
4. Move the application to a dedicated node

Let's implement a memory limit reduction first:

```bash
kubectl patch deployment memory-hog-app -n production -p '{"spec":{"template":{"spec":{"containers":[{"name":"memory-hog-app","resources":{"limits":{"memory":"4Gi"}}}]}}}}'
```

```text
deployment.apps/memory-hog-app patched
```

Let's verify the change:

```bash
kubectl get pods -n production | grep memory-hog
```

```text
memory-hog-app-7d9c4f8b5-2xq9w   1/1     Running   0          45m
memory-hog-app-8a1b2c3d4e-f5g6h   1/1     Running   0          10s
```

The old pod is being terminated and a new one is created. Let's check the new memory usage:

```bash
kubectl top pods -n production | grep memory-hog
```

```text
memory-hog-app-8a1b2c3d4e-f5g6h   150m         3.9Gi
```

The memory usage is now capped at 4Gi. Let's also add a resource quota to prevent future issues:

```bash
kubectl create quota memory-quota -n production --hard=memory=20Gi
```

```text
resourcequota/memory-quota created
```

Let's verify the quota:

```bash
kubectl describe quota memory-quota -n production
```

```text
Name:       memory-quota
Namespace:  production
Resource    Used  Hard
--------    ----  ----
memory      10Gi  20Gi
```

The high memory usage issue has been resolved by:
1. Reducing the memory limit for the memory-hog-app from 8Gi to 4Gi
2. Adding a namespace resource quota to prevent future memory overconsumption