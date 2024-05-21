class Common:
    # logger object
    logger = None
    # control the type of the shufflecad work
    on_real_robot: bool = True

    power: float = 0.0

    # some things
    spi_time_dev: float = 0
    rx_spi_time_dev: float = 0
    tx_spi_time_dev: float = 0
    spi_count_dev: float = 0
    com_time_dev: float = 0
    rx_com_time_dev: float = 0
    tx_com_time_dev: float = 0
    com_count_dev: float = 0
    temperature: float = 0
    memory_load: float = 0
    cpu_load: float = 0