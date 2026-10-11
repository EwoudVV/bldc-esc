cmake_minimum_required(VERSION 3.20)
project(esc_bringup C)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_EXTENSIONS ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(HAL_DIR ${CMAKE_CURRENT_SOURCE_DIR}/vendor/hal)
set(DEVICE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/vendor/stm32g4)
set(HAL_MODULES hal hal_cortex hal_gpio hal_rcc hal_rcc_ex hal_pwr hal_pwr_ex
    hal_flash hal_flash_ex hal_dma hal_dma_ex hal_uart hal_uart_ex hal_spi hal_adc hal_adc_ex)
set(HAL_SOURCES)
foreach(module IN LISTS HAL_MODULES)
  list(APPEND HAL_SOURCES ${HAL_DIR}/Src/stm32g4xx_${module}.c)
endforeach()
add_library(stm32_support STATIC ${HAL_SOURCES} ${DEVICE_DIR}/Source/Templates/system_stm32g4xx.c)
target_include_directories(stm32_support PUBLIC include ${HAL_DIR}/Inc ${DEVICE_DIR}/Include vendor/cmsis/Include)
target_compile_definitions(stm32_support PUBLIC STM32G474xx USE_HAL_DRIVER HSE_VALUE=8000000U USER_VECT_TAB_ADDRESS)
set(ARCH_FLAGS -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard)
target_compile_options(stm32_support PUBLIC ${ARCH_FLAGS} -ffunction-sections -fdata-sections -ffreestanding -fno-builtin)
target_compile_options(stm32_support PRIVATE -Os)
add_executable(esc_bringup src/startup.c src/safe_io.c src/board.c src/main.c src/console.c src/commands.c src/measurements.c src/runtime.c)
target_compile_options(esc_bringup PRIVATE -Os -g3 -Wall -Wextra -Werror -Wno-override-init
    -ffile-prefix-map=${CMAKE_CURRENT_SOURCE_DIR}=firmware -fdebug-prefix-map=${CMAKE_CURRENT_SOURCE_DIR}=firmware)
target_link_libraries(esc_bringup PRIVATE stm32_support gcc)
target_link_options(esc_bringup PRIVATE ${ARCH_FLAGS} -nostdlib
    -T${CMAKE_CURRENT_SOURCE_DIR}/stm32g474ve.ld -Wl,--gc-sections -Wl,--fatal-warnings
    -Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/esc_bringup.map)
set_target_properties(esc_bringup PROPERTIES SUFFIX .elf LINK_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/stm32g474ve.ld)
add_custom_command(TARGET esc_bringup POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:esc_bringup> ${CMAKE_CURRENT_BINARY_DIR}/esc_bringup.bin
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE:esc_bringup>)
