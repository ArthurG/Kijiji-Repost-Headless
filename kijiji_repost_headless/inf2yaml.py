import argparse
import os

import yaml


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert old inf ad format to new yaml ad format. "
                                                 "Please double check converted yaml file after! "
                                                 "Conversion not guaranteed to be 100% accurate.")
    parser.add_argument('inf_file', nargs='?', default="item.inf", help="Old inf file to convert")
    parser.add_argument('yml_file', nargs='?', default="item.yml", help="New yaml file to create")
    args = parser.parse_args()

    with open(args.inf_file, 'r') as f:
        d = {key: val for line in f for (key, val) in (line.strip().split("="),)}

    # Add new dict keys as copies of existing keys
    d['postAdForm.addressCity'] = d['postAdForm.city']
    d['postAdForm.addressProvince'] = d['postAdForm.province']
    d['postAdForm.addressPostalCode'] = d['postAdForm.postalCode']

    # Rename some dict keys to their new values
    d['topAdDuration'] = d.pop('featuresForm.topAdDuration')

    # Convert csv to list
    d['image_paths'] = [i for i in d.pop('imageCsv').split(',')]

    with open(args.yml_file, 'w+') as f:
        f.write(yaml.dump(d))

    print("\"{}\" inf file converted to \"{}\" yaml file.".format(os.path.basename(args.inf_file), os.path.basename(args.yml_file)))
