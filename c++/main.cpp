#include <blaze/Blaze.h>
#include <iostream>

int main(int arc, const char* argv[])
{

    blaze::DynamicMatrix<int> mat{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};

    // Creating a submatrix and modifying it
    auto submat = submatrix(mat, 1, 1, 2, 2);  // Submatrix starting at (1,1) with size 2x2
    submat *= 2;  // Double all elements in the submatrix

    std::cout << "Modified matrix:\n" << mat << std::endl;
    std::cout << "Hello Encounterra!" << std::endl;
    return 0;
}