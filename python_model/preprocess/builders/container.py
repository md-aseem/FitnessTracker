from python_model.preprocess.properties import InputConfig, ContainerSpecs


def build_container_specs(input_config: InputConfig, library_data) -> ContainerSpecs:
    """
    The code to build container config.
    """
    quantum = f"quantum_{input_config.quantum}"

    return ContainerSpecs(container_wall_area = library_data['containers'][quantum]['container_wall_area'],
                          radiation_surface_prcnt= library_data['containers'][quantum]['radiation_surface_prcnt'],
                          container_wall_UA = library_data['containers'][quantum]['container_wall_UA'],
                          container_wall_prcnt_steel = library_data['containers'][quantum]['container_wall_prcnt_steel'],)