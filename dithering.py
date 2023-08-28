import hou
import numpy as np
import array
import inlinecpp

def output_planes_to_cook(cop_node):
    return ("C", "A")

def required_input_planes(cop_node, output_plane):
    if output_plane == "C":
        return ("0", "C")
    
    if output_plane == "A":
        return ("0", "A")
        
    return ()

def resolution(cop_node):
    return __resolution(cop_node)

def depth(cop_node, plane):
    return __depth(cop_node, plane)

def cook(cop_node, plane, resolution):
    if plane == "A":
        return __cook_A(cop_node, plane, resolution)

    if plane == "C":
        return __cook_C(cop_node, plane, resolution)


# internal

def __resolution(cop_node):
    if len(cop_node.inputs()) == 0:
        power = cop_node.parm("power").eval()
        return (2**power, 2**power)
    
    input_node = cop_node.inputs()[0]
    return ( input_node.xRes(), input_node.yRes() )

def __depth(cop_node, plane):
    if len(cop_node.inputs()) == 0:
        return hou.imageDepth.Float32

    img_depth = cop_node.inputs()[0].depth(plane)

    if img_depth != hou.imageDepth.Float32:
        raise hou.NodeError("Invalid color depth. Convert to float32")

    return img_depth

def __cook_C (cop_node, plane, resolution):
    mat_array = __generate_matrix(cop_node)

    if len(cop_node.inputs()) == 0:
        mat_array = np.repeat(np.reshape(mat_array, (resolution[0], resolution[1], 1)), 3, axis=2)
        return cop_node.setPixelsOfCookingPlaneFromString(mat_array)

    input_cop = cop_node.inputs()[0]

    cpp_lib = inlinecpp.createLibrary("py_bayer_dither_cop", function_sources=["""
    void bayer_dither(float *out, float *matrix, int matrix_size, int w, int h)
    {
        int num_pixels = w * h;
        int matrix_len = matrix_size;

        for (int i=0; i < num_pixels ; i++)
        {

            int x = i % w; 
            int y = i / w; 

            int index = (y%matrix_size) * matrix_len + (x%matrix_size);

            float dither_val = matrix[index];

            out[0] = out[0] >= dither_val ? out[0] : out[0] * .5;
            out[1] = out[1] >= dither_val ? out[1] : out[1] * .5;
            out[2] = out[2] >= dither_val ? out[2] : out[2] * .5;

            out += 3;
        }
    }

    """])

    color_pixels = array.array("f", input_cop.allPixelsAsString(plane))

    cpp_lib.bayer_dither(
        color_pixels.buffer_info()[0],
        mat_array.buffer_info()[0],
        __get_mat_size(cop_node),
        resolution[0],
        resolution[1])

    if len(color_pixels) != resolution[0] * resolution[1] * 3:
        color_pixels = array.array("f", [0, 0, 0] * (resolution[0] * resolution[1]))

    cop_node.setPixelsOfCookingPlaneFromString(color_pixels)


def __cook_A (cop_node, plane, resolution):
    if len(cop_node.inputs()) == 0:
        pixels = array.array("f", [0] * (resolution[0] * resolution[1]))
        return cop_node.setPixelsOfCookingPlaneFromString(pixels)

    input_cop = cop_node.inputs()[0]
    pixels = array.array("f", input_cop.allPixelsAsString(plane))

    if len(pixels) != resolution[0] * resolution[1]:
        pixels = array.array("f", [0] * (resolution[0] * resolution[1]))

    cop_node.setPixelsOfCookingPlaneFromString(pixels)
# utils

def __generate_matrix(cop_node):
    power = cop_node.parm("power").eval()
    rotate_times = cop_node.parm("rotate").eval()
    transpose = cop_node.parm("transpose").eval()

    size = 2 ** power
    mat_len = size ** 2

    values = np.matrix(__bayer_matrix(size, power))
    values = np.vectorize(lambda m: m / mat_len)(values)

    if transpose:
        values = np.transpose(values)

    values = np.rot90(values, rotate_times)
    return array.array("f", np.squeeze(np.array(values.reshape(1, mat_len))))

def __get_mat_size(cop_node):
    power = cop_node.parm("power").eval()
    size = 2 ** power
    return size

# https://gamedev.stackexchange.com/questions/130696/how-to-generate-bayer-matrix-of-arbitrary-size

def __bit_reverse(x, n):
    return int(bin(x)[2:].zfill(n)[::-1], 2)

def __bit_interleave(x, y, n):
    x = bin(x)[2:].zfill(n)
    y = bin(y)[2:].zfill(n)
    return int(''.join(''.join(i) for i in zip(x, y)), 2)

def bayer_entry(x, y, n):
    return __bit_reverse(__bit_interleave(x ^ y, y, n), 2*n)

def __bayer_matrix(n, p):
    return [[bayer_entry(x, y, p) for x in range(n)] for y in range(n)]