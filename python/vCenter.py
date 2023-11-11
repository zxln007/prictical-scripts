from pyVim.connect import SmartConnect, Disconnect, SmartConnectNoSSL
from pyVmomi import vim
from asset import models
import atexit
class Vmware:
    def __init__(self, ip, user, password, port, idc, vcenter_id):
        self.ip = ip
        self.user = user
        self.password = password
        self.port = port
        self.idc_id = idc
        self.vcenter_id = vcenter_id
    
    def get_obj(self, content, vimtype, name=None):
        '''
        列表返回,name 可以指定匹配的对象
        '''
        container = content.viewManager.CreateContainerView(content.rootFolder,vimtype, True)
        obj = [ view for view in container.view ]
        return obj
    def get_esxi_info(self):
        # 宿主机信息
        esxi_host = {}
        res = {"connect_status": True, "msg": None}
        try:
        # connect this thing
            si = SmartConnectNoSSL(host=self.ip, user=self.user,
            pwd=self.password, port=self.port, connectionPoolTimeout=60)
        except Exception as e:
            res['connect_status'] = False
        try:
            res['msg'] = ("%s Caught vmodl fault : " + e.msg) % (self.ip)
        except Exception as e:
            res['msg'] = '%s: connection error' % (self.ip)
            return res
# disconnect this thing
        atexit.register(Disconnect, si)
        content = si.RetrieveContent()
        esxi_obj = self.get_obj(content, [vim.HostSystem])
        for esxi in esxi_obj:
            esxi_host[esxi.name] = {}
            esxi_host[esxi.name]['idc_id'] = self.idc_id
            esxi_host[esxi.name]['vcenter_id'] = self.vcenter_id
            esxi_host[esxi.name]['server_ip'] = esxi.name
            esxi_host[esxi.name]['manufacturer'] = esxi.summary.hardware.vendor
            esxi_host[esxi.name]['server_model'] = esxi.summary.hardware.model
        for i in esxi.summary.hardware.otherIdentifyingInfo:
            if isinstance(i, vim.host.SystemIdentificationInfo):
                esxi_host[esxi.name]['server_sn'] = i.identifierValue
                # 系统名称
                esxi_host[esxi.name]['system_name'] = esxi.summary.config.product.fullName
                # cpu总核数
                esxi_cpu_total = esxi.summary.hardware.numCpuThreads
                # 内存总量 GB
                esxi_memory_total = esxi.summary.hardware.memorySize / 1024 / 1024 /1024
                # 获取硬盘总量 GB
                esxi_disk_total = 0
        for ds in esxi.datastore:
            esxi_disk_total += ds.summary.capacity / 1024 / 1024 / 1024
            # 默认配置4核8G100G，根据这个配置计算剩余可分配虚拟机
            default_configure = {
                'cpu': 4,
                'memory': 8,
                'disk': 100
                }
            esxi_host[esxi.name]['vm_host'] = []
            vm_usage_total_cpu = 0
            vm_usage_total_memory = 0
            vm_usage_total_disk = 0
# 虚拟机信息
        for vm in esxi.vm:
            host_info = {}
            host_info['vm_name'] = vm.name
            host_info['power_status'] = vm.runtime.powerState
            host_info['cpu_total_kernel'] = str(vm.config.hardware.numCPU) + '核'
            host_info['memory_total'] = str(vm.config.hardware.memoryMB) + 'MB'
            host_info['system_info'] = vm.config.guestFullName
            disk_info = ''
            disk_total = 0
        for d in vm.config.hardware.device:
            if isinstance(d, vim.vm.device.VirtualDisk):
                disk_total += d.capacityInKB / 1024 / 1024
                disk_info += d.deviceInfo.label + ": " + str((d.capacityInKB) / 1024 / 1024) + ' GB' + ','
                host_info['disk_info'] = disk_info
                esxi_host[esxi.name]['vm_host'].append(host_info)
# 计算当前宿主机可用容量：总量 - 已分配的
            if host_info['power_status'] == 'poweredOn':
                vm_usage_total_cpu += vm.config.hardware.numCPU
                vm_usage_total_disk += disk_total
                vm_usage_total_memory += (vm.config.hardware.memoryMB /
                1024)
                esxi_cpu_free = esxi_cpu_total - vm_usage_total_cpu
                esxi_memory_free = esxi_memory_total - vm_usage_total_memory
                esxi_disk_free = esxi_disk_total - vm_usage_total_disk
                esxi_host[esxi.name]['cpu_info'] = 'Total: %d核, Free: %d核' %(esxi_cpu_total, esxi_cpu_free)
                esxi_host[esxi.name]['memory_info'] = 'Total: %dGB, Free: %dGB' %(esxi_memory_total, esxi_memory_free)
                esxi_host[esxi.name]['disk_info'] = 'Total: %dGB, Free: %dGB' %(esxi_disk_total, esxi_disk_free)
# 计算cpu 内存 磁盘按照默认资源分配的最小值，即为当前可分配资源
            if esxi_cpu_free < 4 or esxi_memory_free < 8 or esxi_disk_free < 100:
                free_allocation_vm_host = 0
            else:
                free_allocation_vm_host = int(min(
                    [
                        esxi_cpu_free / default_configure['cpu'],
                        esxi_memory_free / default_configure['memory'],
                        esxi_disk_free / default_configure['disk']
                    ]
                ))
                esxi_host[esxi.name]['free_allocation_vm_host'] = free_allocation_vm_host
                esxi_host['connect_status'] = True
                return esxi_host
    def write_to_db(self):
        esxi_host = self.get_esxi_info()
        # 连接失败
        if not esxi_host['connect_status']:
            return esxi_host
        del esxi_host['connect_status']
        for machine_ip in esxi_host:
        # 物理机信息
            esxi_host_dict = esxi_host[machine_ip]
        # 虚拟机信息
            virtual_host = esxi_host[machine_ip]['vm_host']
            del esxi_host[machine_ip]['vm_host']
            obj = models.EsxiHost.objects.create(**esxi_host_dict)
            obj.save()
            for host_info in virtual_host:
                host_info['management_host_id'] = obj.id
                obj2 = models.virtualHost.objects.create(**host_info)
                obj2.save()
