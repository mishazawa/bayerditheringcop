#include <UT/UT_DSOVersion.h>
#include <HOM/HOM_Module.h>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <string>
#include <new>

namespace inlinecpp {
template <typename T>
class Array
{
public:
    Array()
    {
        clear();
    }

    Array(const T *pointer, int num_elements)
    {
        clear();
        set(pointer, num_elements);
    }

    Array(const std::vector<T> &values)
    {
        clear();
        set(values);
    }

    Array(const std::string &str)
    {
        clear();
        if (str.size() != 0)
            set(&str[0], str.size());
    }

    template <typename U>
    Array(const std::vector<std::vector<U> > &values)
    {
        clear();
        set(values);
    }

    Array(const std::vector<std::string> &values)
    {
        clear();
        set(values);
    }

    void set(const T *pointer, int num_elements)
    {
        if (num_elements == 0)
            return;

        allocate_array(num_elements);
        memcpy(const_cast<T *>(pointer_), pointer, sizeof(T) * num_elements);
    }

    void set(const std::vector<T> &values)
    {
        if (values.size() != 0)
            set(&values[0], values.size());
    }

    template <typename U>
    void set(const std::vector<std::vector<U> > &values)
    {
        if (values.size() == 0)
            return;

        // Note that T is Array<U>.
        allocate_array(values.size());
        for (int i=0; i<values.size(); ++i)
            new (const_cast<T *>(&pointer_[i])) T(values[i]);
    }

    void set(const std::vector<std::string> &values)
    {
        if (values.size() == 0)
            return;

        // Note that T is Array<char>.
        allocate_array(values.size());
        for (int i=0; i<values.size(); ++i)
            new (const_cast<T *>(&pointer_[i])) T(values[i]);
    }

private:
    void clear()
    {
        pointer_ = NULL;
        num_elements_ = 0;
        padding_ = 0;
    }

    void allocate_array(int num_elements)
    {
        pointer_ = (T *)malloc(sizeof(T) * num_elements);
        num_elements_ = num_elements;
    }

    const T *pointer_;
    int num_elements_;

    // This padding member is a hack to work around problems with MSVC on
    // 32-bit machines.  On these machines, when returning (by value) a C++
    // struct (or even a C++ class without any constructors) that is 8 bytes
    // big, it will place the result in registers eax and edx.  However, when
    // returning an 8 byte C++ class that contains constructors, it will
    // instead put the 8 bytes above the stack and set eax to point to the
    // stack variable.  Unfortunately, ctypes (via libffi) looks for the return
    // value in the registers, so we'll read garbage from functions returning
    // inlinecpp::Array objects.
    //
    // So, to work around the problem we make the size of the struct larger
    // than 8 bytes so libffi knows that the return value won't be in
    // registers.
    int padding_;
};

typedef Array<char> BinaryString;
typedef Array<char> String;

template <typename T>
inline BinaryString as_binary_string(const std::vector<T> &values)
{
    return BinaryString((const char *)&values[0], values.size() * sizeof(T));
}

inline BinaryString as_binary_string(const char *c_string)
{
    return BinaryString(c_string, strlen(c_string));
}

inline String as_string(const char *c_string)
{
    return as_binary_string(c_string);
}

} //namespace


__declspec(dllexport) 
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

            out[0] *= out[0] >= dither_val ? 1 /*out[0]*/ : .5;
            out[1] *= out[1] >= dither_val ? 1 /*out[1]*/ : .5;
            out[2] *= out[2] >= dither_val ? 1 /*out[2]*/ : .5;

            out += 3;
        }
    }

    
