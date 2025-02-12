# ansible/roles/common/tasks/main.yml
---
- name: Update system packages
  apt:
    update_cache: yes
    cache_valid_time: "{{ update_cache_valid_time }}"
    
- name: Install required system packages
  apt:
    name: "{{ system_packages }}"
    state: present
    
- name: Set timezone
  timezone:
    name: "{{ timezone }}"
    
- name: Configure locale
  locale_gen:
    name: "{{ locale }}"
    state: present

- name: Create SPLAT directories
  file:
    path: "{{ item }}"
    state: directory
    mode: '0755'
  with_items:
    - "{{ splat_base_path }}"
    - "{{ ground_control_data_path }}"
    - "{{ ground_control_config_path }}"
    - "{{ ground_control_logs_path }}"

# ansible/roles/security/tasks/main.yml
---
- name: Configure UFW
  ufw:
    state: enabled
    policy: deny
  when: ufw_enabled | bool

- name: Allow required ports
  ufw:
    rule: allow
    port: "{{ item }}"
  with_items: "{{ allowed_ports }}"
  when: ufw_enabled | bool

- name: Configure SSH hardening
  template:
    src: sshd_config.j2
    dest: /etc/ssh/sshd_config
    mode: '0600'
  notify: Restart SSH

- name: Install security packages
  apt:
    name:
      - fail2ban
      - unattended-upgrades
    state: present

- name: Configure automatic security updates
  template:
    src: auto_upgrades.j2
    dest: /etc/apt/apt.conf.d/20auto-upgrades
    mode: '0644'

# ansible/roles/docker/tasks/main.yml
---
- name: Install Docker prerequisites
  apt:
    name:
      - apt-transport-https
      - ca-certificates
      - curl
      - gnupg
      - lsb-release
    state: present

- name: Add Docker GPG key
  apt_key:
    url: https://download.docker.com/linux/debian/gpg
    state: present

- name: Add Docker repository
  apt_repository:
    repo: deb [arch=arm64] https://download.docker.com/linux/debian bullseye stable
    state: present

- name: Install Docker
  apt:
    name:
      - docker-ce
      - docker-ce-cli
      - containerd.io
    state: present

- name: Install Docker Compose
  get_url:
    url: "https://github.com/docker/compose/releases/download/v{{ docker_compose_version }}/docker-compose-linux-aarch64"
    dest: /usr/local/bin/docker-compose
    mode: '0755'

- name: Add users to Docker group
  user:
    name: "{{ item }}"
    groups: docker
    append: yes
  with_items: "{{ docker_users }}"

# ansible/roles/lora/tasks/main.yml
---
- name: Install LoRa dependencies
  apt:
    name:
      - python3-pip
      - python3-rpi.gpio
      - python3-spidev
    state: present

- name: Enable SPI interface
  lineinfile:
    path: /boot/config.txt
    line: "dtoverlay=spi0-hw-cs"
    state: present
  notify: Reboot system

- name: Configure LoRa pins
  template:
    src: lora_config.j2
    dest: "{{ ground_control_config_path }}/lora.yml"
    mode: '0644'

- name: Install Python LoRa libraries
  pip:
    name:
      - RPi.GPIO
      - spidev
      - adafruit-circuitpython-rfm9x
    state: present

# ansible/roles/ground_control/tasks/main.yml
---
- name: Pull Ground Control images
  docker_compose:
    project_src: "{{ splat_base_path }}"
    build: no
    pull: yes
  tags: ['docker']

- name: Configure Ground Control
  template:
    src: ground_control.yml.j2
    dest: "{{ ground_control_config_path }}/config.yml"
    mode: '0644'
  notify: Restart Ground Control

- name: Deploy Docker Compose configuration
  template:
    src: docker-compose.yml.j2
    dest: "{{ splat_base_path }}/docker-compose.yml"
    mode: '0644'
  notify: Restart Ground Control

- name: Start Ground Control services
  docker_compose:
    project_src: "{{ splat_base_path }}"
    state: present
  tags: ['docker']

- name: Wait for Ground Control to be ready
  uri:
    url: "http://localhost:{{ ground_control_port }}/health"
    return_content: yes
  register: health_check
  until: health_check.status == 200
  retries: "{{ health_check_retries }}"
  delay: "{{ health_check_delay }}"

# ansible/roles/monitoring/tasks/main.yml
---
- name: Install monitoring stack
  docker_compose:
    project_src: "{{ splat_base_path }}"
    services:
      - prometheus
      - grafana
      - node-exporter
    state: present
  when: monitoring_enabled | bool

- name: Configure Prometheus
  template:
    src: prometheus.yml.j2
    dest: "{{ ground_control_config_path }}/prometheus.yml"
    mode: '0644'
  notify: Restart Prometheus
  when: monitoring_enabled | bool

- name: Configure Grafana
  template:
    src: grafana.ini.j2
    dest: "{{ ground_control_config_path }}/grafana.ini"
    mode: '0644'
  notify: Restart Grafana
  when: monitoring_enabled | bool

- name: Deploy Grafana dashboards
  copy:
    src: "dashboards/{{ item }}"
    dest: "{{ ground_control_config_path }}/dashboards/"
    mode: '0644'
  with_items:
    - ground_control.json
    - lora_metrics.json
    - system_metrics.json
  when: monitoring_enabled | bool

# ansible/roles/backup/tasks/main.yml
---
- name: Create backup directory
  file:
    path: "{{ backup_path }}"
    state: directory
    mode: '0755'
  when: backup_enabled | bool

- name: Configure backup script
  template:
    src: backup.sh.j2
    dest: /usr/local/bin/splat-backup
    mode: '0755'
  when: backup_enabled | bool

- name: Setup backup cron job
  cron:
    name: "SPLAT Backup"
    job: "/usr/local/bin/splat-backup"
    hour: "2"
    minute: "0"
  when: backup_enabled | bool

- name: Configure backup retention
  template:
    src: cleanup.sh.j2
    dest: /usr/local/bin/splat-cleanup
    mode: '0755'
  when: backup_enabled | bool

# Common handlers for all roles
# ansible/roles/handlers/main.yml
---
- name: Restart SSH
  service:
    name: sshd
    state: restarted

- name: Reboot system
  reboot:
    reboot_timeout: 300

- name: Restart Ground Control
  docker_compose:
    project_src: "{{ splat_base_path }}"
    services:
      - ground_control
    state: restarted

- name: Restart Prometheus
  docker_compose:
    project_src: "{{ splat_base_path }}"
    services:
      - prometheus
    state: restarted
  when: monitoring_enabled | bool

- name: Restart Grafana
  docker_compose:
    project_src: "{{ splat_base_path }}"
    services:
      - grafana
    state: restarted
  when: monitoring_enabled | bool
