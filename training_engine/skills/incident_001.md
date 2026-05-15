# Incident: Pod CrashLoopBackOff

# Prompt
A pod in the production namespace is in CrashLoopBackOff state. Investigate and resolve the issue.

# Investigation Steps

Let's first check the pod status:

```bash
kubectl get pods -n production
```

```text
NAME                             READY   STATUS             RESTARTS   AGE
nginx-deployment-7fb7c8b4b-2w9x8   0/1     CrashLoopBackOff   5          3m15s
nginx-deployment-7fb7c8b4b-5k2m9   0/1     CrashLoopBackOff   5          3m15s
```

Let's get more details about the pod:

```bash
kubectl describe pod nginx-deployment-7fb7c8b4b-2w9x8 -n production
```

```text
Name:         nginx-deployment-7fb7c8b4b-2w9x8
Namespace:    production
Priority:     0
Node:         worker-node-1/10.0.1.4
Start Time:   Mon, 15 May 2026 10:30:45 +0000
Labels:       app=nginx
              pod-template-hash=7fb7c8b4b
Annotations:  <none>
Status:       Running
IP:           10.244.1.15
IPs:
  IP:  10.244.1.15
Containers:
  nginx:
    Container ID:   containerd://abc123def456
    Image:          nginx:latest
    Image ID:       docker.io/library/nginx@sha256:xyz789
    Port:           80/TCP
    Host Port:      0/TCP
    State:          Waiting
      Reason:       CrashLoopBackOff
    Last State:     Terminated
      Reason:       Error
      Exit Code:    1
    Ready:          False
    Restart Count:  5
    Environment:    <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-xyz (ro)
Conditions:
  Type              Status
  Initialized       True
  Ready             False
  ContainersReady   False
  PodScheduled      True
...
Events:
  Type     Reason     Age                    From               Message
  ----     ------     ----                   ----               -------
  Normal   Scheduled  4m                     default-scheduler  Successfully assigned production/nginx-deployment-7fb7c8b4b-2w9x8 to worker-node-1
  Normal   Pulling    4m                     kubelet            Pulling image "nginx:latest"
  Normal   Pulled     3m                     kubelet            Successfully pulled image "nginx:latest" in 1.23456789s
  Normal   Created    3m (x4 over 4m)        kubelet            Created container nginx
  Normal   Started    3m (x4 over 4m)        kubelet            Started container nginx
  Warning  BackOff    2m (x10 over 4m)       kubelet            Back-off restarting failed container
```

Let's check the logs to see what's causing the crash:

```bash
kubectl logs nginx-deployment-7fb7c8b4b-2w9x8 -n production
```

```text
2026/05/15 10:31:15 [emerg] 1#1: mkdir() "/var/cache/nginx/client_temp" failed (13: Permission denied)
nginx: [emerg] mkdir() "/var/cache/nginx/client_temp" failed (13: Permission denied)
```

The issue is clear now. The nginx container is trying to create directories but doesn't have permission. Let's check the deployment configuration:

```bash
kubectl get deployment nginx-deployment -n production -o yaml
```

```text
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
        securityContext:
          runAsUser: 1000
          runAsGroup: 1000
```

# Resolution
The issue is that the nginx container is running as user 1000, but nginx needs to write to /var/cache/nginx which is owned by root. We need to either:
1. Run the container as root (not recommended for security)
2. Add an init container to fix permissions
3. Use a custom nginx image with proper permissions

Let's fix it by adding an init container:

```bash
kubectl patch deployment nginx-deployment -n production -p '{"spec":{"template":{"spec":{"initContainers":[{"name":"fix-permissions","image":"busybox","command":["sh","-c","chown -R 1000:1000 /var/cache/nginx /var/log/nginx /var/run"],"volumeMounts":[{"name":"nginx-cache","mountPath":"/var/cache/nginx"},{"name":"nginx-log","mountPath":"/var/log/nginx"},{"name":"nginx-run","mountPath":"/var/run"}]}],"volumes":[{"name":"nginx-cache","emptyDir":{}},{"name":"nginx-log","emptyDir":{}},{"name":"nginx-run","emptyDir":{}}]}}}}'
```

```text
deployment.apps/nginx-deployment patched
```

Let's verify the fix:

```bash
kubectl get pods -n production
```

```text
NAME                             READY   STATUS    RESTARTS   AGE
nginx-deployment-7fb7c8b4b-2w9x8   1/1     Running   0          10s
nginx-deployment-7fb7c8b4b-5k2m9   1/1     Running   0          10s
```

The pods are now running successfully. Issue resolved.