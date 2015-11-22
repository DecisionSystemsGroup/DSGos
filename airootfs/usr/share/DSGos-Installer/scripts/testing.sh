#!/bin/bash

previous="/tmp/dev-setup"
uefi="/sys/firmware/efi"
vbox_chk="$(hwinfo --gfxcard | grep -o -m 1 "VirtualBox")"
arg="$1"
check_keys="$(pacman-key -l | grep DSGos)"

notify_user () {

       sudo -u DSGos notify-send -t 10000 -a "DSGos_Installer" -i /usr/share/DSGos_Installer/data/images/DSGos/DSGos-icon.png "$1"
}

do_update () {

# Update DSGos_Installer with latest testing code
	echo "Removing existing DSGos_Installer..."
	killall python
	mv  /usr/share/DSGos_Installer /usr/share/DSGos_Installer.old;
	if [[ ${development} = "True" ]]; then

		notify_user "Getting latest version of DSGos_Installer from development branch..."
		echo "Getting latest version of DSGos_Installer from development branch..."
		# Check commandline arguments to choose repo
		#if [ "$1" = "-d" ] || [ "$1" = "--dev-repo" ]; then
		#	git clone https://github.com/"$2"/DSGos_Installer.git DSGos_Installer;
		#else
		#	git clone https://github.com/DSGos/DSGos_Installer.git DSGos_Installer;
		#fi
		cd /tmp
		{ wget http://DSGos.org/DSGos_Installer.tar && tar -xf DSGos_Installer.tar && cp -R DSGos_Installer /usr/share && rm DSGos_Installer.tar \
		 	&& rm -Rf DSGos_Installer && cd /usr/share/DSGos_Installer && return 0; } || \
		{ mv  /usr/share/DSGos_Installer.old /usr/share/DSGos_Installer && notify_user "Something went wrong. Update failed." \
		 && return 1; }
	else
		notify_user "Getting latest version of DSGos_Installer from stable branch..."
		echo "Getting latest version of DSGos_Installer from stable branch..."
		{ pacman -Syy --noconfirm DSGos_Installer && return 0; } || { mv  /usr/share/DSGos_Installer.old /usr/share/DSGos_Installer \
		&& notify_user "Something went wrong. Update failed." && return 1; }
	fi

}

start_DSGos_Installer () {

	# Start DSGos_Installer with appropriate options
	notify_user "Starting DSGos_Installer..."
	echo "Starting DSGos_Installer..."
	if [[ ${development} = "True" ]]; then
		DSGos_Installer -d -v -p /usr/share/DSGos_Installer/data/packages.xml &
		exit 0;


	else

		DSGos_Installer -d -v &
		exit 0;

	fi

}

if [[ ${arg} = "development" ]]; then
	development=True
else
	stable=True
fi
# Check if this is the first time we are executed.
if ! [ -f "${previous}" ]; then
	touch ${previous};
	# Find the best mirrors (fastest and latest)
#    notify_user "Selecting the best mirrors..."
#	echo "Selecting the best mirrors..."
#	echo "Testing Arch mirrors..."
#	reflector -p http -l 30 -f 5 --save /etc/pacman.d/mirrorlist;
#	echo "Done."
#	sudo -u DSGos wget http://DSGos.info/DSGos-mirrorlist
#	echo "Testing DSGos mirrors..."
#	rankmirrors -n 0 -r DSGos DSGos-mirrorlist > /tmp/DSGos-mirrorlist
#	cp /tmp/DSGos-mirrorlist /etc/pacman.d/
#	echo "Done."
	if [[ ${check_keys} = '' ]]; then
	pacman-key --init
	pacman-key --populate archlinux DSGos
	fi

	# Install any packages that haven't been added to the iso yet but are needed.
	notify_user "Installing missing packages..."
	echo "Installing missing packages..."
	# Check if system is UEFI boot.
	if [ -d "${uefi}" ]; then
		pacman -Syy git efibootmgr --noconfirm --needed;
	else
		pacman -Syy git --noconfirm --needed;
	fi
	# Enable kernel modules and other services
	if [[ "${vbox_chk}" == "VirtualBox" ]] && [ -d "${uefi}" ]; then
		echo "VirtualBox detected. Checking kernel modules and starting services."
		modprobe -a vboxsf f2fs efivarfs dm-mod && systemctl restart vboxservice;
	elif [[ "${vbox_chk}" == "VirtualBox" ]]; then
		modprobe -a vboxsf f2fs dm-mod && systemctl restart vboxservice;
	else
		modprobe -a f2fs dm-mod;
	fi
	
else
    notify_user "Previous testing setup detected, skipping downloads..."
	echo "Previous testing setup detected, skipping downloads..."
	echo "Verifying that nothing is mounted from a previous install attempt."
	umount -lf /install/boot >/dev/null 2&>1
	umount -lf /install >/dev/null 2&>1

fi


do_update && start_DSGos_Installer


exit 1;
