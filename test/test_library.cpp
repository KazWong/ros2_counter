#include "ros2_counter/library.hpp"

#include <cassert>

int main() {
    assert(ros2_counter::add_integers(2, 3) == 5);
    return 0;
}
