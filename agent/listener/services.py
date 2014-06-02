import nodes
import platform
import subprocess
import logging
import tempfile


def filter_services(m):
    def wrapper(*args, **kwargs):
        services = m(*args, **kwargs)
        filter_services = kwargs.get('service', [])
        filter_statuses = kwargs.get('status', [])
        if filter_services or filter_statuses:
            accepted = {}
            if filter_services:
                for service in filter_services:
                    if service in services:
                        accepted[service] = services[service]
            if filter_statuses:
                for service in services:
                    if services[service] in filter_statuses:
                        accepted[service] = services[service]
            return accepted
        return services
    return wrapper


class ServiceNode(nodes.LazyNode):

    def get_service_method(self, *args, **kwargs):
        uname = platform.uname()[0]
        try:
            process = subprocess.Popen(['which', 'systemctl'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait()
            if process.returncode == 0:
                is_systemctl = True
            else:
                is_systemctl = False
        except:
            is_systemctl = False

        if uname == 'Windows':
            return self.get_services_via_sc
        elif uname == 'Darwin':
            return self.get_services_via_launchctl
        else:
            if is_systemctl:
                return self.get_services_via_systemctl
            else:
                return self.get_services_via_initd

    @filter_services
    def get_services_via_sc(self, *args, **kwargs):
        services = {}
        status = tempfile.TemporaryFile()
        service = subprocess.Popen(['sc', 'query', 'type=', 'service', 'state=', 'all'], stdout=status)
        service.wait()
        status.seek(0)

        for line in status.readlines():
            l = line.strip()
            if l.startswith('SERVICE_NAME'):
                service_name = l.split(' ', 1)[1]
            if l.startswith('STATE'):
                if 'RUNNING' in l:
                    status = 'running'
                else:
                    status = 'stopped'
                services[service_name] = status
        return services

    @filter_services
    def get_services_via_launchctl(self, *args, **kwargs):
        services = {}
        status = tempfile.TemporaryFile()
        service = subprocess.Popen(['launchctl', 'list'], stdout=status)
        service.wait()
        status.seek(0)
        # The first line is the header
        status.readline()

        for line in status.readlines():
            pid, status, label = line.split()
            if pid == '-':
                services[label] = 'stopped'
            elif status == '-':
                services[label] = 'running'
        return services

    @filter_services
    def get_services_via_systemctl(self, *args, **kwargs):
        pass

    @filter_services
    def get_services_via_initd(self, *args, **kwargs):
        services = {}
        disabled_keywords = ['stopped', 'not', 'disabled']
        status = tempfile.TemporaryFile()
        service = subprocess.Popen(['service', '--status-all'], stdout=status)
        service.wait()
        status.seek(0)

        for line in status.readlines():
            for keyword in disabled_keywords:
                if keyword in line:
                    pass
        return services

    def walk(self, *args, **kwargs):
        if kwargs.get('first', True):
            self.method = self.get_service_method(*args, **kwargs)
            return {self.name: self.method(*args, **kwargs)}
        else:
            return {self.name: []}

    @staticmethod
    def get_service_name(request_args):
        service_name = request_args.get('service', [])
        return service_name

    @staticmethod
    def get_target_status(request_args):
        target_status = request_args.get('status', [])
        return target_status

    @staticmethod
    def make_stdout(returncode, stdout_builder):
        if returncode == 0:
            prefix = 'OK'
        else:
            prefix = 'CRITICAL'

        prioritized_stdout = sorted(stdout_builder, key=lambda x: x['priority'], reverse=True)
        info_line = ', '.join([x['info'] for x in prioritized_stdout])

        stdout = '%s: %s' % (prefix, info_line)
        return stdout

    def run_check(self, *args, **kwargs):
        service_names = self.get_service_name(kwargs)
        target_statuses = self.get_target_status(kwargs)
        method = self.get_service_method(*args, **kwargs)

        services = method(*args, **kwargs)
        returncode = 0
        status = 'not a problem'
        stdout_builder = []
        for service in service_names:
            priority = 0
            if service in services:
                status = services[service]
                builder = 'Service %s is %s' % (service, status)
                if not status in target_statuses:
                    priority = 1
            else:
                priority = 2
                builder = 'Service %s was not found' % service

            if priority > returncode:
                returncode = priority

            stdout_builder.append({'info': builder, 'priority': priority})

        if returncode > 0:
            returncode = 2
        stdout = self.make_stdout(returncode, stdout_builder)
        return {'stdout': stdout, 'returncode': returncode}


