# Windows counterpart. On this Mac lab, use ./scripts/q10-detect.sh.
# Looks for RIM USB (VID 0FCA) and a 169.254.* BlackBerry adapter.
$usb = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
  Where-Object { $_.InstanceId -match 'VID_0FCA' -or $_.FriendlyName -match 'BlackBerry' }
$net = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
  Where-Object { $_.IPAddress -like '169.254.*' }
Write-Output "PHONE_USB_PRESENT     $(if ($usb) { 'yes' } else { 'no' })"
Write-Output "USB_NETWORK_PRESENT   $(if ($net) { 'yes' } else { 'no' })"
if ($net) {
  Write-Output "HOST_IP               $($net[0].IPAddress)"
}
Write-Output "DEPLOY_AVAILABLE      $(if (Get-Command blackberry-deploy -ErrorAction SilentlyContinue) { 'yes' } else { 'no' })"
Write-Output "SSH_AVAILABLE         no"
Write-Output "NOTE                  Device IP must be probed; do not assume 169.254.0.1"
