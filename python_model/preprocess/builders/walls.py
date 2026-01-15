from python_model.preprocess.properties import WallSpecs
from python_model.preprocess.loaders import load_input_config, load_library_data


def build_wall_specs(input_config, library_data):

    quantum = f"quantum_{input_config.quantum}"

    steel_wall_area = (library_data['containers'][quantum]['container_wall_area'] *
                   library_data['containers'][quantum]['steel_wall']['percent_total_area'])

    steel_wall_mass = (steel_wall_area * library_data['containers'][quantum]['steel_wall']['thickness'] *
                       library_data['containers'][quantum]['steel_wall']['density'])

    steel_wall_specs = WallSpecs(rho=library_data['containers'][quantum]['steel_wall']['density'],
                                  area=steel_wall_area,
                                  mass=steel_wall_mass,
                                  cp=library_data['containers'][quantum]['steel_wall']['cp'],
                                  k=library_data['containers'][quantum]['steel_wall']['conductivity'],
                                  thickness=library_data['containers'][quantum]['steel_wall']['thickness'])

    insulation_wall_area = (library_data['containers'][quantum]['container_wall_area'] *
                   library_data['containers'][quantum]['insulation_wall']['percent_total_area'])

    insulation_wall_mass = (insulation_wall_area * library_data['containers'][quantum]['insulation_wall']['thickness'] *
                       library_data['containers'][quantum]['insulation_wall']['density'])

    insulation_wall_specs = WallSpecs(rho=library_data['containers'][quantum]['insulation_wall']['density'],
                                  area=insulation_wall_area,
                                  mass=insulation_wall_mass,
                                  cp=library_data['containers'][quantum]['insulation_wall']['cp'],
                                  k=library_data['containers'][quantum]['insulation_wall']['conductivity'],
                                  thickness=library_data['containers'][quantum]['insulation_wall']['thickness'])

    return steel_wall_specs, insulation_wall_specs


if __name__ == "__main__":
    input_config = load_input_config()
    library_data = load_library_data()
    steel_wall_specs, insulation_wall_specs = build_wall_specs(input_config, library_data)