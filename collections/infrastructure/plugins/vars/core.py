from ansible.plugins.vars import BaseVarsPlugin


class VarsModule(BaseVarsPlugin):

    def get_vars(self, loader, path, entities, cache=True):

        super(VarsModule, self).get_vars(loader, path, entities)
        data = {

            # Core version: 3.2.1
            'bb_core_iceberg_naming': 'iceberg',
            'bb_core_equipment_naming': 'equipment',
            'bb_core_os_naming': 'os',
            'bb_core_hw_naming': 'hw',
            'bb_core_management_networks_naming': 'net',
            'bb_core_master_groups_naming': 'fn',
            'bb_core_managements_group_name': 'fn_management',

            # ############################################################
            # ########### J2_ LOGIC
            # ####

            # ## Network

            # List of management networks.
            'j2_management_networks': "{{ networks | select('match','^'+bb_core_management_networks_naming+'-[a-zA-Z0-9]+') | list | unique | sort }}",

            # # Resolution
            # Resolution network. The network on which host can be ping by direct name. (ex: ping c001).
            'j2_node_main_resolution_network': "{{ network_interfaces[0].network | default(none) }}",
            # Resolution address.
            'j2_node_main_resolution_address': "{{ (network_interfaces[0].ip4 | default('')).split('/')[0] | default(none) }}",

            # # Main network
            # The network used by Ansible to deploy configuration (related to ssh).
            # Also the network used by the host to get services ip.
            # This network must have 3 keys defined at least: network, interface, and ip4, to be considered valid as main network.
            'j2_node_main_network': "{{ network_interfaces | default([]) | selectattr('network','defined') | selectattr('interface','defined') | selectattr('ip4','defined') | selectattr('network','match','^'+bb_core_management_networks_naming+'-[a-zA-Z0-9]+') | map(attribute='network') | list | first | default(none) }}",
            # Main network interface. For consistency, we use j2_node_main_network as source.
            'j2_node_main_network_interface': "{{ network_interfaces | default([]) | selectattr('network','defined') | selectattr('interface','defined') | selectattr('ip4','defined') | selectattr('network','match','^'+bb_core_management_networks_naming+'-[a-zA-Z0-9]+') | map(attribute='interface') | list | first | default(none) }}",
            # Main address, same concept.
            'j2_node_main_address': "{{ network_interfaces | default([]) | selectattr('network','defined') | selectattr('interface','defined') | selectattr('ip4','defined') | selectattr('network','match','^'+bb_core_management_networks_naming+'-[a-zA-Z0-9]+') | map(attribute='ip4') | list | first | default(none) }}",

            # Generate the nodes list, as a cache for network_interfaces
            # Example:
            # c001:
            #     alias: null
            #     bmc:
            #         ip4: 10.10.103.1
            #         mac: 2a:2b:3c:2d:5e:6f
            #         name: bc001
            #         network: net-admin
            #     current_iceberg: iceberg1
            #     global_alias: null
            #     icebergs_main_network_dict: null
            #     network_interfaces:
            #     - interface: enp1s0
            #         ip4: 10.10.3.1
            #         mac: 1a:2b:3c:4d:5e:9f
            #         network: net-admin
            #     node_main_resolution_address: 10.10.3.1
            # This is a transverse j2 (j2_bb_), used as a cache fact
            # An optimisation is made so that icebergs_main_network_dict is only calculated for management nodes (because its slow)
            # Note for me: TODO icebergs_main_network_dict must disapear, find how.
            'j2_bb_nodes': """{%- set bnodes = {} -%}
            {%- for host in j2_hosts_range -%}
              {% set hostvars_buffer = hostvars[host] %}
              {%- do bnodes.update({
                host: {
                  'network_interfaces': hostvars_buffer['network_interfaces'] | default(none, true),
                  'node_main_resolution_address': hostvars_buffer['j2_node_main_resolution_address'] | default(none, true),
                  'current_iceberg': hostvars_buffer['j2_current_iceberg'] | default(none, true),
                  'bmc': hostvars_buffer['bmc'] | default(none, true),
                  'alias': hostvars_buffer['alias'] | default(none, true)
                }
              }) -%}
            {%- endfor -%}
            {{ bnodes }}""",

            # # Equipments
            # Generate the list of nodes with their associated os and hw groups as values, along their equipment profile ep
            # Example:
            #   c001:
            #     hw: hw_supermicro_XXX
            #     os: os_ubuntu_22.04_gpu
            #     ep: hw_supermicro_XXX_with_os_ubuntu_22.04_gpu
            # This is a transverse j2 (j2_bb_), used as a cache fact
            'j2_bb_nodes_profiles': """{%- set bnodes_profiles = {} -%}
            {%- for host in j2_hosts_range -%}
              {%- set host_hw = (hostvars[host]['group_names'] | select('match','^'+bb_core_hw_naming+'_.*') | list | unique | sort | first) | default(none, true) -%}
              {%- set host_os = (hostvars[host]['group_names'] | select('match','^'+bb_core_os_naming+'_.*') | list | unique | sort | first) | default(none, true) -%}
              {%- set host_type = hostvars[host]['hw_equipment_type'] | default(none, true) -%}
              {%- if host_hw is not none and host_os is not none -%}
                {%- set host_ep = (host_hw + '_with_' + host_os) -%}
              {%- else -%}
                {%- set host_ep = none -%}
              {%- endif -%}
              {%- do bnodes_profiles.update({host: {'hw': host_hw, 'os': host_os, 'ep': host_ep, 'type': host_type}}) -%}
            {%- endfor -%}
            {{ bnodes_profiles }}""",

            # Generate the equipments that are existing combination of hardware and os profiles
            # and store the list of associated nodes inside these equipments. Nodes without both hw_ and os_ are ignored.
            # This dict also contains all os_ and hw_ values for this equipment profile ep.
            # This is based on the BlueBanquise rule that os_ and hw_ values MUST be set at these groups level only.
            # Example:
            #   hw_supermicro_XXX_with_os_ubuntu_22.04_gpu: # -> can easily deduce hw and os group names from that
            #     nodes:
            #       - c001
            #       - c002
            #     hw:
            #       hw_equipment_type: server
            #       hw_console: ...
            #     os:
            #       os_operating_system: ...
            # This is a transverse j2 (j2_bb_), used as a cache fact
            # It is expected that the dependency fact be bb_nodes_profiles
            # If the dependency fact was not already cached, it will not be used but that implies longuer calculations
            # generic equipment does not inherit any hw or os values, so should rely on the roles default ones
            'j2_bb_equipments': """{%- set bequipments = {} -%}
            {%- if bb_nodes_profiles is defined -%}
              {%- set bnodes_profiles = bb_nodes_profiles -%}
            {%- else -%}{# Calculate since not cached #}
              {%- set bnodes_profiles = j2_bb_nodes_profiles -%}
            {%- endif -%}
            {%- for host, host_keys in bnodes_profiles.items() -%}
              {%- if host_keys['ep'] is not none -%}
                {%- if host_keys['ep'] not in bequipments -%}
                  {%- set os_settings = {} -%}
                  {%- set first_host_of_group_vars = hostvars[groups[host_keys['os']][0]] -%}
                  {%- for osvalue in (first_host_of_group_vars | select('match','^os_.*')) -%}
                    {%- do os_settings.update({osvalue: first_host_of_group_vars[osvalue]}) -%}
                  {%- endfor -%}
                  {%- set hw_settings = {} -%}
                  {%- set first_host_of_group_vars = hostvars[groups[host_keys['hw']][0]] -%}
                  {%- for hwvalue in (first_host_of_group_vars | select('match','^hw.*')) -%}
                    {%- do hw_settings.update({hwvalue: first_host_of_group_vars[hwvalue]}) -%}
                  {%- endfor -%}
                  {%- do bequipments.update({host_keys['ep']: {'nodes': [], 'hw': hw_settings, 'os': os_settings}}) -%}
                {%- endif -%}
            {{ bequipments[host_keys['ep']]['nodes'].append(host) }}
              {%- else -%}
                {%- if 'generic' not in bequipments -%}
                  {%- do bequipments.update({'generic': {'nodes': [], 'hw': {}, 'os': {}}}) -%}
                {%- endif -%}
            {{ bequipments['generic']['nodes'].append(host) }}
              {%- endif -%}
            {%- endfor -%}
            {{ bequipments }}""",

            # ## Icebergs
            # Grab current iceberg group
            'j2_current_iceberg': "{{ bb_icebergs | default(false) | ternary( group_names | select('match','^'+bb_core_iceberg_naming+'[a-zA-Z0-9]+') | list | unique | sort | first | default(bb_core_iceberg_naming+'1'), bb_core_iceberg_naming+'1') }}",
            # Grab current iceberg number
            'j2_current_iceberg_number': "{{ j2_current_iceberg | replace(bb_core_iceberg_naming,' ') | trim }}",
            # Generate range of hosts to include in current configurations
            'j2_hosts_range': "{{ ((bb_icebergs | default(false)) == true) | ternary( (groups[j2_current_iceberg] | default([])), groups['all']) }}",
            # List all icebergs
            'j2_icebergs_groups_list': "{{ groups | select('match','^'+bb_core_iceberg_naming+'[a-zA-Z0-9]+') | list }}",
            # Get total number of icebergs
            'j2_number_of_icebergs': "{{ groups | select('match','^'+bb_core_iceberg_naming+'[a-zA-Z0-9]+') | list | length }}"
        }
        return data
