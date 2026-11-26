#pragma once

#include <string>
#include <utility>

#include "tapa/base/task.h"

namespace tapa {

struct executable {
  explicit executable(std::string path);
};

struct task {
#if defined(TAPA_TARGET_DEVICE_) || defined(TAPA_TARGET_XILINX_HLS_) || defined(__SYNTHESIS__)
  template <typename Func, typename... Args>
  task& invoke(Func&&, Args&&...) { return *this; }

  template <internal::InvokeMode mode, typename Func, typename... Args>
  task& invoke(Func&&, Args&&...) { return *this; }

  template <typename Func, typename... Args, size_t name_size>
  task& invoke(Func&&, const char (&)[name_size], Args&&...) { return *this; }

  template <internal::InvokeMode mode, typename Func, typename... Args,
            size_t name_size>
  task& invoke(Func&&, const char (&)[name_size], Args&&...) { return *this; }

  template <internal::InvokeMode mode, int n, typename Func, typename... Args>
  task& invoke(Func&&, Args&&...) { return *this; }

  template <internal::InvokeMode mode, int n, typename Func, typename... Args,
            size_t name_size>
  task& invoke(Func&&, const char (&)[name_size], Args&&...) { return *this; }

  template <typename Func, typename... Args>
  task& invoke(Func&&, executable, Args&&...) { return *this; }
#else
  template <typename Func, typename... Args>
  task& invoke(Func&& func, Args&&... args) {
    return invoke<join>(std::forward<Func>(func), "",
                        std::forward<Args>(args)...);
  }

  template <internal::InvokeMode mode, typename Func, typename... Args>
  task& invoke(Func&& func, Args&&... args) {
    return invoke<mode>(std::forward<Func>(func), "",
                        std::forward<Args>(args)...);
  }

  template <typename Func, typename... Args, size_t name_size>
  task& invoke(Func&& func, const char (&name)[name_size], Args&&... args) {
    return invoke<join>(std::forward<Func>(func), name,
                        std::forward<Args>(args)...);
  }

  template <internal::InvokeMode mode, typename Func, typename... Args,
            size_t name_size>
  task& invoke(Func&& func, const char (&name)[name_size], Args&&... args) {
    func(std::forward<Args>(args)...);
    return *this;
  }

  template <internal::InvokeMode mode, int n, typename Func, typename... Args>
  task& invoke(Func&& func, Args&&... args) {
    return invoke<mode, n>(std::forward<Func>(func), "",
                           std::forward<Args>(args)...);
  }

  template <internal::InvokeMode mode, int n, typename Func, typename... Args,
            size_t name_size>
  task& invoke(Func&& func, const char (&name)[name_size], Args&&... args) {
    for (int i = 0; i < n; ++i) {
      invoke<mode>(std::forward<Func>(func), std::forward<Args>(args)...);
    }
    return *this;
  }

  template <typename Func, typename... Args>
  task& invoke(Func&& func, executable exe, Args&&... args) {
    return invoke<join>(std::forward<Func>(func), "",
                        std::forward<Args>(args)...);
  }
#endif
};

}  // namespace tapa
