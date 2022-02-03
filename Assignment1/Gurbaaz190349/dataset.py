"""dataset.py: A python file implementing image transformation functions and creating augmented dataset
using the transformations"""

__author__ = "Gurbaaz Singh Nandra"


import os
import sys
import random
import logging
import pickle
import numpy as np
from PIL import Image
from tqdm import tqdm


CIFAR_DATASET_FILENAME = "cifar-10-batches-py"
IMAGES_PER_BATCH = 10000
NUM_TRAIN_BATCHES = 5
HEIGHT = 32
CHANNELS = 3


def enable_logging() -> logging.Logger:
    """
    Returns a formatted logger for stdout and file io.
    """
    LOG_FILE = "dataset.log"
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    # formatter = logging.Formatter("%(levelname)s - %(asctime)s\n%(message)s")
    formatter = logging.Formatter("%(message)s")

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    log.addHandler(stdout_handler)
    log.addHandler(file_handler)

    return log


def unpickle(file):
    """
    Loads the data batch bytefile using pickle
    """
    with open(file, "rb") as f:
        dict = pickle.load(f, encoding="bytes")
    return dict


def random_rotation(input_image):
    """
    Random Rotation in the range [−180 degree, +180 degree]

    Input:
        Input image
    Output:
        Transformed image
    """
    theta = random.randint(-180, 180)

    theta = np.radians(-theta)

    output_image = np.zeros((CHANNELS, HEIGHT, HEIGHT))

    for i in range(0, HEIGHT):
        for j in range(0, HEIGHT):
            cos, sin = np.cos(theta), np.sin(theta)
            ni = np.rint((i - 15.5) * cos + (j - 15.5) * sin + 15.5).astype("uint8")
            nj = np.rint((j - 15.5) * cos - (i - 15.5) * sin + 15.5).astype("uint8")
            if ni >= 0 and ni < 32 and nj >= 0 and nj < 32:
                for channel in range(CHANNELS):
                    output_image[channel][ni][nj] = input_image[channel][i][j]

    return output_image


def random_cutout(input_image):
    """
    Random cutout (randomly erase a block of pixels from the image with the width and height
    of the block in the range 0 to 16 pixels. The erased part (cutout) should be filled with a
    single value)

    Input:
        Input image
    Output:
        Transformed image
    """
    width = random.randint(0, 16)
    height = random.randint(0, 16)
    value = np.random.randint(0, 256, 3)

    ## top-left coordinates
    tlx = random.randint(0, 31 - width)
    tly = random.randint(0, 31 - height)

    ## bottom-right coordinates
    brx = random.randint(tlx, 31)
    bry = random.randint(tly, 31)

    output_image = np.copy(input_image)

    ## random cutout loop
    for channel in range(CHANNELS):
        for i in range(tlx, brx + 1):
            for j in range(tly, bry + 1):
                output_image[channel][i][j] = value[channel]

    return output_image


def random_crop(input_image):
    """
    Random Crop (Add a padding of 2 pixels on all sides and randomly select a block of 32x32
    pixels from the padded image)

    Input:
        Input image
    Output:
        Transformed image
    """
    ## top-left coordinates
    tlx = random.randint(0, 4)
    tly = random.randint(0, 4)

    ## bottom-right coordinates
    brx = tlx + HEIGHT
    bry = tly + HEIGHT

    padded_image = np.zeros((CHANNELS, HEIGHT + 4, HEIGHT + 4))
    output_image = np.zeros((CHANNELS, HEIGHT, HEIGHT))

    for channel in range(CHANNELS):
        padded_image[channel] = np.pad(
            input_image[channel], pad_width=2, mode="constant", constant_values=0
        )

    for channel in range(CHANNELS):
        output_image[channel] = padded_image[channel][tlx:brx, tly:bry]

    return output_image


def contrast_and_horizontal_flipping(input_image):
    """
    Contrast & Horizontal flipping. (First, change the contrast of the image with a factor of
    α randomly selected from the range (0.5, 2.0) and then flip the image horizontally with a
    probability of 0.5)

    Input:
        Input image
    Output:
        Transformed image
    """
    alpha = random.uniform(0.5, 2.0)

    output_image = np.zeros((CHANNELS, HEIGHT, HEIGHT))

    ## perform contrast
    for channel in range(CHANNELS):
        for i in range(0, 32):
            for j in range(0, 32):
                output_image[channel][i][j] = (
                    alpha * (input_image[channel][i][j] - 128) + 128
                )

    output_image = np.clip(output_image, 0, 255)

    probability = random.random()

    if probability > 0.5:
        ## perform horizontal flip
        for channel in range(CHANNELS):
            for i in range(0, HEIGHT):
                for j in range(0, HEIGHT // 2):
                    (
                        output_image[channel][i][j],
                        output_image[channel][i][HEIGHT - 1 - j],
                    ) = (
                        input_image[channel][i][HEIGHT - 1 - j],
                        input_image[channel][i][j],
                    )

    return output_image


def save_image(image, filename):
    """
    Expects a (channels=3, height=32, width=32) shaped numpy array and saves it as image
    """
    Image.fromarray(image.transpose(1, 2, 0).astype(np.uint8)).save(filename)


def main():
    """
    Entry point of script
    """
    log = enable_logging()

    # filenames = []
    labels = []
    images = []

    ## 1. Loading the dataset
    log.info("## 1. Loading the dataset")

    for file in os.listdir(CIFAR_DATASET_FILENAME):
        if file.startswith("data"):
            batch_dataset = unpickle(os.path.join(CIFAR_DATASET_FILENAME, file))

            # filenames.extend(batch_dataset[b"filenames"])
            labels.extend(batch_dataset[b"labels"])
            images.extend(np.array(batch_dataset[b"data"]))

        elif file.startswith("batches"):
            label_names = unpickle(os.path.join(CIFAR_DATASET_FILENAME, file))[
                b"label_names"
            ]
            label_names = [label.decode("utf-8") for label in label_names]

        elif file.startswith("test_batch"):
            test_batch = unpickle(os.path.join(CIFAR_DATASET_FILENAME, file))

            # test_filenames = test_batch[b"filenames"]
            test_labels = test_batch[b"labels"]
            test_images = np.array(test_batch[b"data"])

    unaugmented_dataset = {
        # "filenames": filenames,
        "labels": labels,
        "images": np.array(images).reshape(
            IMAGES_PER_BATCH * NUM_TRAIN_BATCHES, CHANNELS, HEIGHT, HEIGHT
        ),
    }
    test_dataset = {
        # "filenames": test_filenames,
        "labels": test_labels,
        "images": np.array(test_images).reshape(
            IMAGES_PER_BATCH, CHANNELS, HEIGHT, HEIGHT
        ),
    }

    log.info(f"Size of train dataset: {len(unaugmented_dataset['labels'])}")
    # log.info(f"Size of test dataset: {len(test_dataset['filenames'])}")
    log.info(f"Labels in CIFAR-10 dataset: {label_names}")

    log.info("Pickling unaugmented dataset")

    with open("unaugmented_dataset", "wb") as f:
        pickle.dump(unaugmented_dataset, f)

    log.info("Pickling test dataset")

    with open("test_dataset", "wb") as f:
        pickle.dump(test_dataset, f)

    ## 2. Image transformations
    log.info("## 2. Image transformations")

    example_idx = random.randint(0, NUM_TRAIN_BATCHES * IMAGES_PER_BATCH - 1)
    example_image = unaugmented_dataset["images"][example_idx]

    log.info(
        f"Label of example image: {unaugmented_dataset['labels'][example_idx]} ({label_names[unaugmented_dataset['labels'][example_idx]-1]})"
    )
    # log.info(
    #     f"Name of example image: {train_dataset['filenames'][example_idx].decode('utf-8')}"
    # )
    log.info(f"Matrix shape of example image: {example_image.shape}")

    ## Naive approach
    # image_ = np.array([])
    # for j in range(HEIGHT * HEIGHT):
    #    image_ = np.append(image_, example_image[j :: HEIGHT * HEIGHT])

    # image_.resize(32, 32, 3)

    save_image(example_image, "example.png")

    out1 = random_rotation(example_image)
    save_image(out1, "example_randomrotation.png")

    out2 = random_cutout(example_image)
    save_image(out2, "example_randomcutout.png")

    out3 = random_crop(example_image)
    save_image(out3, "example_randomcrop.png")

    out4 = contrast_and_horizontal_flipping(example_image)
    save_image(out4, "example_contrastandhorizontalflip.png")

    log.info(
        "Example image and its transformation images have been saved as .png files"
    )

    ## 3. Generating augmented training set
    log.info("## 3. Generating augmented training dataset")

    operations = np.random.randint(0, 4, NUM_TRAIN_BATCHES * IMAGES_PER_BATCH)
    augmented_images = []

    for i in tqdm(range(NUM_TRAIN_BATCHES * IMAGES_PER_BATCH)):
        # for i in tqdm(range(100)):
        og_image = unaugmented_dataset["images"][i]
        operation = operations[i]

        if operation == 0:
            augmented_image = random_rotation(og_image)
        elif operation == 1:
            augmented_image = random_cutout(og_image)
        elif operation == 2:
            augmented_image = random_crop(og_image)
        else:
            augmented_image = contrast_and_horizontal_flipping(og_image)

        augmented_images.append(augmented_image)

    augmented_dataset = {
        # "filenames": filenames,
        "labels": labels,
        "images": np.array(augmented_images).reshape(
            NUM_TRAIN_BATCHES * IMAGES_PER_BATCH, CHANNELS, HEIGHT, HEIGHT
        ),
        # "images": np.array(augmented_images).reshape(100, CHANNELS, HEIGHT, HEIGHT),
    }

    log.info(f"Size of train dataset: {len(augmented_dataset['labels'])}")

    log.info("Pickling augmented dataset")

    with open("augmented_dataset", "wb") as f:
        pickle.dump(augmented_dataset, f)

    return 0


if __name__ == "__main__":
    sys.exit(main())
