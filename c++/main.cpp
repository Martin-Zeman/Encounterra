#include <blaze/Blaze.h>
#include <iostream>

enum class Size { MEDIUM = 1, LARGE = 2, HUGE = 3, GARGANTUAN = 4 };

struct Coord { int x, y; };

void moveUsingSubmatrix(blaze::DynamicMatrix<int>& grid, Size size, Coord oldPos, Coord newPos, int id) {
    int sizeVal = static_cast<int>(size);
    auto oldSubmatrix = submatrix(grid, oldPos.x, oldPos.y, sizeVal, sizeVal);
    oldSubmatrix = -1;
    auto newSubmatrix = submatrix(grid, newPos.x, newPos.y, sizeVal, sizeVal);
    newSubmatrix = id;
}

void moveUsingIndividualAccess(blaze::DynamicMatrix<int>& grid, Size size, Coord oldPos, Coord newPos, int id) {
    int sizeVal = static_cast<int>(size);
    for (int i = 0; i < sizeVal; ++i) {
        for (int j = 0; j < sizeVal; ++j) {
            grid(oldPos.x + i, oldPos.y + j) = -1;
            grid(newPos.x + i, newPos.y + j) = id;
        }
    }
}

double runBenchmark(auto&& func, blaze::DynamicMatrix<int>& grid, Size size, 
                    const std::vector<std::pair<Coord, Coord>>& moves, int numIterations) {
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < numIterations; ++i) {
        for (const auto& [oldPos, newPos] : moves) {
            func(grid, size, oldPos, newPos, i + 1);
        }
    }
    auto end = std::chrono::high_resolution_clock::now();
    return std::chrono::duration<double, std::milli>(end - start).count();
}

int main(int arc, const char* argv[])
{
    const int gridSize = 15;
    const int numMoves = 1000;
    const int numIterations = 100;
    std::vector<Size> sizes = {Size::MEDIUM, Size::LARGE, Size::HUGE, Size::GARGANTUAN};

    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, gridSize - 5);  // -5 to ensure space for largest size

    for (Size size : sizes) {
        blaze::DynamicMatrix<int> grid(gridSize, gridSize, -1);
        std::vector<std::pair<Coord, Coord>> moves;

        for (int i = 0; i < numMoves; ++i) {
            moves.push_back({{dis(gen), dis(gen)}, {dis(gen), dis(gen)}});
        }

        double submatrixTime = runBenchmark(moveUsingSubmatrix, grid, size, moves, numIterations);
        double individualTime = runBenchmark(moveUsingIndividualAccess, grid, size, moves, numIterations);

        std::cout << "Size: " << static_cast<int>(size) << "x" << static_cast<int>(size) << std::endl;
        std::cout << "Submatrix approach: " << submatrixTime << " ms" << std::endl;
        std::cout << "Individual access: " << individualTime << " ms" << std::endl;
        std::cout << "Ratio (Submatrix/Individual): " << submatrixTime / individualTime << std::endl;
        std::cout << std::endl;
    }

    return 0;


    // blaze::DynamicMatrix<int> mat{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};

    // // Creating a submatrix and modifying it
    // auto submat = submatrix(mat, 1, 1, 2, 2);  // Submatrix starting at (1,1) with size 2x2
    // submat *= 2;  // Double all elements in the submatrix

    // std::cout << "Modified matrix:\n" << mat << std::endl;
    // std::cout << "Hello Encounterra!" << std::endl;
    // return 0;
}