#!/bin/bash

# Xác định màu sắc ANSI
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Print header
echo -e "\n${BOLD}===============================================${NC}"
echo -e "${BOLD}      MikroTik Monitor - Trình cài đặt tự động      ${NC}"
echo -e "${BOLD}===============================================${NC}\n"

# Kiểm tra OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Kiểm tra phiên bản Ubuntu
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" ]]; then
            echo -e "${GREEN}Phát hiện: Ubuntu ${VERSION_ID}${NC}"
            
            # Kiểm tra phiên bản Ubuntu 24.04
            if [[ "$VERSION_ID" == "24.04" ]]; then
                echo -e "${GREEN}Phiên bản Ubuntu 24.04 được hỗ trợ.${NC}"
                echo -e "Sẽ sử dụng install_ubuntu_24.04.sh để cài đặt."
                
                # Kiểm tra quyền sudo
                if [[ $EUID -ne 0 ]]; then
                    echo -e "${RED}Script này cần chạy với quyền root.${NC}"
                    echo -e "Vui lòng chạy lại với sudo: ${BOLD}sudo ./install.sh${NC}"
                    exit 1
                fi
                
                # Cấp quyền thực thi cho script cài đặt Ubuntu
                chmod +x install_ubuntu_24.04.sh
                
                # Chạy script cài đặt Ubuntu
                ./install_ubuntu_24.04.sh
                exit $?
            else
                echo -e "${YELLOW}Phiên bản Ubuntu của bạn (${VERSION_ID}) không phải là phiên bản chính thức được hỗ trợ (24.04).${NC}"
                echo -e "Bạn có thể gặp một số vấn đề khi cài đặt."
                echo -e "Bạn có muốn tiếp tục với script cài đặt cho Ubuntu 24.04? (y/n)"
                read -r response
                if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                    # Kiểm tra quyền sudo
                    if [[ $EUID -ne 0 ]]; then
                        echo -e "${RED}Script này cần chạy với quyền root.${NC}"
                        echo -e "Vui lòng chạy lại với sudo: ${BOLD}sudo ./install.sh${NC}"
                        exit 1
                    fi
                    
                    # Cấp quyền thực thi cho script cài đặt Ubuntu
                    chmod +x install_ubuntu_24.04.sh
                    
                    # Chạy script cài đặt Ubuntu
                    ./install_ubuntu_24.04.sh
                    exit $?
                else
                    echo -e "${YELLOW}Cài đặt bị hủy.${NC}"
                    exit 0
                fi
            fi
        else
            echo -e "${YELLOW}Hệ thống Linux của bạn (${ID}) không phải là Ubuntu.${NC}"
            echo -e "Bạn có thể thử cài đặt theo hướng dẫn thủ công trong file INSTALLATION.md"
            echo -e "hoặc sử dụng Docker với docker-compose.yml."
            
            echo -e "\nBạn có muốn sử dụng Docker để cài đặt? (y/n)"
            read -r response
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                echo -e "${GREEN}Đang kiểm tra Docker và Docker Compose...${NC}"
                
                # Kiểm tra Docker
                if ! command -v docker &> /dev/null; then
                    echo -e "${RED}Docker chưa được cài đặt.${NC}"
                    echo -e "Vui lòng cài đặt Docker trước: https://docs.docker.com/engine/install/"
                    exit 1
                fi
                
                # Kiểm tra Docker Compose
                if ! command -v docker-compose &> /dev/null; then
                    echo -e "${RED}Docker Compose chưa được cài đặt.${NC}"
                    echo -e "Vui lòng cài đặt Docker Compose trước: https://docs.docker.com/compose/install/"
                    exit 1
                fi
                
                echo -e "${GREEN}Đang khởi động ứng dụng với Docker Compose...${NC}"
                docker-compose up -d
                
                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}Ứng dụng đã được khởi động thành công với Docker!${NC}"
                    echo -e "Truy cập tại: ${BOLD}http://localhost:5000${NC}"
                    echo -e "\nThông tin đăng nhập mặc định:"
                    echo -e "  Username: ${BOLD}admin${NC}"
                    echo -e "  Password: ${BOLD}admin123${NC}"
                    echo -e "${RED}Hãy đổi mật khẩu mặc định ngay sau khi đăng nhập!${NC}"
                else
                    echo -e "${RED}Có lỗi xảy ra khi khởi động ứng dụng với Docker.${NC}"
                    echo -e "Vui lòng kiểm tra logs: ${BOLD}docker-compose logs${NC}"
                fi
                
                exit $?
            else
                echo -e "${YELLOW}Cài đặt bị hủy.${NC}"
                exit 0
            fi
        fi
    else
        echo -e "${RED}Không thể xác định phiên bản Linux.${NC}"
        echo -e "Vui lòng xem file INSTALLATION.md để cài đặt thủ công."
        exit 1
    fi
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo -e "${GREEN}Phát hiện: Windows${NC}"
    echo -e "Cài đặt trên Windows yêu cầu PowerShell với quyền Administrator."
    echo -e "\nVui lòng mở PowerShell với quyền Administrator và chạy:"
    echo -e "${BOLD}Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass${NC}"
    echo -e "${BOLD}.\install_windows.ps1${NC}"
    exit 0
else
    echo -e "${RED}Hệ điều hành không được hỗ trợ: $OSTYPE${NC}"
    echo -e "MikroTik Monitor hiện chỉ hỗ trợ Ubuntu 24.04 và Windows."
    echo -e "Vui lòng xem file INSTALLATION.md để cài đặt thủ công hoặc thử dùng Docker."
    exit 1
fi