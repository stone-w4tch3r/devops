### Prerequisites:
* Windows 10 ISO
* WindowsADK Deployment Tools

### Build ISO:
1. Mount Windows 10 ISO
2. Copy contents to ISO_DIR (e.g. C:\win10-ansible-ready)
3. Add Autounattend.xml to ISO_DIR
4. Put scripts in ISO_DIR\sources\$OEM$\$$\Setup\Scripts
    > $OEM$ is a special folder name https://superuser.com/a/1534756
5. Open Deployment and Imaging Tools Environment
6. Run the following command to pack the ISO:
    ```
    oscdimg.exe -lwin10-ansible-ready -m -u2 -bC:\win10-ansible-ready\boot\etfsboot.com C:\win10-ansible-ready C:\win10-ansible-ready.iso
    ```

### Resources:
* https://madlabber.wordpress.com/2019/06/19/using-autounattend-xml-to-enable-ansible-support-in-windows/
* https://www.catapultsystems.com/blogs/create-zero-touch-windows-10-iso/
* https://medium.com/@ikelca/create-bootable-iso-with-oscdimg-359d7c6194c3